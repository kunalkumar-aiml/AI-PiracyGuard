"""Scan orchestration services.

Orchestrates running the ForensicAnalysis pipeline, storing results in database,
and querying history/statistics.
"""

from datetime import datetime, timezone
import os
from typing import Dict, Any, List, Optional

from sqlalchemy.orm import Session

from piracyguard.config import settings
from piracyguard.core.detection_engine import DetectionEngine
from piracyguard.core.fingerprint.engine import VideoFingerprint, FingerprintEngine
from piracyguard.database.models import Fingerprint, ScanJob, ScanResult, JobStatus, RiskLevel
from piracyguard.exceptions import VideoNotFoundError, ProcessingError
from piracyguard.logging_config import get_logger

logger = get_logger(__name__)


class ScanService:
    """Service to manage video scanning, registration, and reporting details."""

    def __init__(self, detection_engine: Optional[DetectionEngine] = None) -> None:
        self.engine = detection_engine or DetectionEngine()

    def register_reference_video(self, db: Session, video_path: str, user_id: Optional[int] = None) -> Fingerprint:
        """Generate and save reference fingerprint for a known original video.

        Args:
            db: Database session.
            video_path: Absolute or relative path to reference video.
            user_id: ID of the user who registered the video.

        Returns:
            Saved Fingerprint ORM object.

        Raises:
            VideoNotFoundError: If file does not exist.
            ProcessingError: If fingerprint generation fails.
        """
        if not os.path.exists(video_path):
            raise VideoNotFoundError(video_path)

        logger.info("Registering reference video", extra={"video_path": video_path})

        # Generate fingerprint
        fp = self.engine.fp_engine.generate(video_path)
        if not fp:
            raise ProcessingError(f"Failed to generate fingerprint for reference video: {video_path}")

        # Map to ORM model
        db_fp = Fingerprint(
            video_path=video_path,
            video_hash=hash(fp.temporal),  # Basic fast hash
            fingerprint_ahash="|".join(fp.ahashes),
            fingerprint_phash="|".join(fp.phashes),
            fingerprint_dhash="|".join(fp.dhashes),
            fingerprint_temporal=fp.temporal,
            frame_count=fp.frame_count,
            duration_seconds=fp.duration_seconds,
            registered_by=user_id
        )

        db.add(db_fp)
        db.commit()
        db.refresh(db_fp)
        logger.info("Reference video registered successfully", extra={"video_path": video_path, "uuid": db_fp.uuid})
        return db_fp

    def get_known_fingerprints(self, db: Session) -> Dict[str, VideoFingerprint]:
        """Fetch all stored reference fingerprints from database."""
        db_fps = db.query(Fingerprint).all()
        result = {}

        for db_fp in db_fps:
            # Map back to VideoFingerprint dataclass
            fp = VideoFingerprint(
                video_path=db_fp.video_path,
                ahashes=db_fp.fingerprint_ahash.split("|") if db_fp.fingerprint_ahash else [],
                phashes=db_fp.fingerprint_phash.split("|") if db_fp.fingerprint_phash else [],
                dhashes=db_fp.fingerprint_dhash.split("|") if db_fp.fingerprint_dhash else [],
                temporal=db_fp.fingerprint_temporal or "",
                frame_count=db_fp.frame_count or 0,
                duration_seconds=db_fp.duration_seconds or 0.0
            )
            result[db_fp.video_path] = fp

        return result

    def scan_video(self, db: Session, video_path: str, job_id: int) -> ScanResult:
        """Execute the forensic check on a single video file.

        Args:
            db: Database session.
            video_path: Path of the target video to analyze.
            job_id: ID of the ScanJob execution tracking this scan.

        Returns:
            Saved ScanResult ORM object.
        """
        logger.info("Executing forensic scan on video", extra={"video_path": video_path, "job_id": job_id})

        # Load reference fingerprints
        known_fps = self.get_known_fingerprints(db)

        # Run pipeline
        analysis = self.engine.check_video(video_path, known_fps)

        # Save to database
        db_result = ScanResult(
            job_id=job_id,
            video_path=analysis.video_path,
            similarity_score=analysis.similarity_score,
            matched_video_path=analysis.matched_video_path,
            deepfake_score=analysis.deepfake.deepfake_score,
            deepfake_confidence=analysis.deepfake.confidence,
            deepfake_model_used=analysis.deepfake.model_used,
            watermark_present_score=analysis.watermark.watermark_present_score,
            watermark_tampering_score=analysis.watermark.tampering_score,
            watermark_confidence=analysis.watermark.confidence,
            metadata_anomaly_score=analysis.metadata.anomaly_score,
            metadata_details=analysis.metadata.details,
            ocr_results={
                "extracted_texts": analysis.ocr.extracted_texts,
                "confidence_scores": analysis.ocr.confidence_scores
            },
            logo_detections={
                "detections": analysis.logo.detections
            },
            risk_score=analysis.risk.risk_score,
            risk_level=analysis.risk.risk_level,
            risk_confidence=analysis.risk.confidence,
            risk_explanation=analysis.risk.explanation,
            recommended_action=analysis.risk.recommended_action
        )

        db.add(db_result)
        db.commit()
        db.refresh(db_result)

        logger.info(
            "Forensic scan result stored in database",
            extra={
                "video_path": video_path,
                "result_uuid": db_result.uuid,
                "risk_level": db_result.risk_level.value
            }
        )

        return db_result

    def get_stats(self, db: Session) -> Dict[str, Any]:
        """Generate summary statistics of scan history."""
        total_registered = db.query(Fingerprint).count()
        total_scans = db.query(ScanResult).count()
        
        high_risk = db.query(ScanResult).filter(ScanResult.risk_level == RiskLevel.HIGH).count()
        critical_risk = db.query(ScanResult).filter(ScanResult.risk_level == RiskLevel.CRITICAL).count()
        medium_risk = db.query(ScanResult).filter(ScanResult.risk_level == RiskLevel.MEDIUM).count()
        low_risk = db.query(ScanResult).filter(ScanResult.risk_level == RiskLevel.LOW).count()

        return {
            "total_registered_videos": total_registered,
            "total_scans": total_scans,
            "threat_distribution": {
                "CRITICAL": critical_risk,
                "HIGH": high_risk,
                "MEDIUM": medium_risk,
                "LOW": low_risk,
                "NONE": max(0, total_scans - (critical_risk + high_risk + medium_risk + low_risk))
            },
            "status": "ACTIVE"
        }
