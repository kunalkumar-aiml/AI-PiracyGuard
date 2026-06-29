"""Orchestrator for AI-PiracyGuard forensics checks.

Coordinates fingerprinting, deepfake classification, watermark scanning,
and metadata analytics to compile a comprehensive ForensicAnalysis profile.
"""

from dataclasses import dataclass
from typing import Dict, Any, List, Optional
import time

from piracyguard.config import settings
from piracyguard.core.fingerprint.engine import FingerprintEngine, VideoFingerprint
from piracyguard.core.deepfake.detector import DeepfakeDetector, DeepfakeResult
from piracyguard.core.watermark.analyzer import WatermarkAnalyzer, WatermarkResult
from piracyguard.core.metadata.video_metadata import MetadataAnalyzer, MetadataResult
from piracyguard.core.ocr.text_extractor import OCRExtractor, OCRResult
from piracyguard.core.logo.logo_detector import LogoDetector, LogoResult
from piracyguard.core.risk_engine import RiskEngine, RiskAssessment
from piracyguard.logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class ForensicAnalysis:
    """Dataclass holding complete video forensics analysis output."""
    video_path: str
    duration_seconds: float
    fingerprint: Optional[VideoFingerprint]
    similarity_score: float
    matched_video_path: Optional[str]
    deepfake: DeepfakeResult
    watermark: WatermarkResult
    metadata: MetadataResult
    ocr: OCRResult
    logo: LogoResult
    risk: RiskAssessment
    analysis_duration_seconds: float


class DetectionEngine:
    """Forensic pipeline orchestrator that coordinates all scanners."""

    def __init__(
        self,
        fingerprint_engine: Optional[FingerprintEngine] = None,
        deepfake_detector: Optional[DeepfakeDetector] = None,
        watermark_analyzer: Optional[WatermarkAnalyzer] = None,
        metadata_analyzer: Optional[MetadataAnalyzer] = None,
        ocr_extractor: Optional[OCRExtractor] = None,
        logo_detector: Optional[LogoDetector] = None
    ) -> None:
        self.fp_engine = fingerprint_engine or FingerprintEngine()
        self.df_detector = deepfake_detector or DeepfakeDetector()
        self.wm_analyzer = watermark_analyzer or WatermarkAnalyzer()
        self.meta_analyzer = metadata_analyzer or MetadataAnalyzer()
        self.ocr_extractor = ocr_extractor or OCRExtractor()
        self.logo_detector = logo_detector or LogoDetector()

    def check_video(
        self,
        video_path: str,
        known_fingerprints: Dict[str, VideoFingerprint],
        step: Optional[int] = None
    ) -> ForensicAnalysis:
        """Run the full media forensics pipeline on a video file.

        Args:
            video_path: Path to the target video file.
            known_fingerprints: Dictionary mapping paths to reference fingerprints.
            step: Sampling interval (overrides config).

        Returns:
            ForensicAnalysis profile containing detailed metrics.
        """
        logger.info(
            "Starting media forensics pipeline",
            extra={"video_path": video_path}
        )
        start_time = time.time()
        sample_step = step or settings.FRAME_SAMPLE_STEP

        # 1. Generate fingerprint for target video
        target_fp = self.fp_engine.generate(video_path, step=sample_step)

        # 2. Compare against reference fingerprints database
        highest_similarity = 0.0
        matched_path: Optional[str] = None

        if target_fp and known_fingerprints:
            for ref_path, ref_fp in known_fingerprints.items():
                # Avoid self-matching
                if ref_path == video_path:
                    continue
                
                similarity = self.fp_engine.compare(target_fp, ref_fp)
                if similarity > highest_similarity:
                    highest_similarity = similarity
                    matched_path = ref_path

        # 3. Run Deepfake Face Analysis
        deepfake_res = self.df_detector.analyze(video_path, step=sample_step)

        # 4. Run Watermark & Steganography checks
        watermark_res = self.wm_analyzer.analyze(video_path, step=sample_step)

        # 5. Run Metadata Forensics
        metadata_res = self.meta_analyzer.analyze(video_path)

        # 6. Run OCR Text Extraction on the first frame
        # (Optimize by OCR'ing a subset of frames to speed up processing)
        # We extract frames using OpenCV directly for OCR / Logo check to avoid overhead
        ocr_result = OCRResult(extracted_texts=[], confidence_scores=[], regions=[])
        logo_result = LogoResult(detections=[], confidence_scores=[], detected_count=0)

        # Retrieve a few sample frames for overlay analysis
        sample_frames = self.df_detector.extractor.extract_uniform(
            video_path, step=sample_step * 2, max_frames=3
        )
        
        ocr_flagged = False
        logo_detected = False

        if sample_frames:
            # Analyze overlays on the first sampled frame
            _, _, sample_frame = sample_frames[0]
            
            # OCR
            ocr_result = self.ocr_extractor.extract(sample_frame)
            # Flag if unauthorized keywords are extracted (e.g. copyright notices)
            for text in ocr_result.extracted_texts:
                if any(kw in text.lower() for kw in ["copy", "all rights", "unauthorized", "leak"]):
                    ocr_flagged = True
                    break

            # Logo overlays
            logo_result = self.logo_detector.detect(sample_frame)
            if logo_result.detected_count > 0:
                logo_detected = True

        # 7. Compute Composite Risk Profile
        risk_res = RiskEngine.assess(
            similarity_score=highest_similarity,
            deepfake_score=deepfake_res.deepfake_score,
            watermark_present_score=watermark_res.watermark_present_score,
            watermark_tampering_score=watermark_res.tampering_score,
            metadata_anomaly_score=metadata_res.anomaly_score,
            audio_anomaly_score=0.0,  # Audio analyzer is Phase 3
            logo_detected=logo_detected,
            ocr_flagged=ocr_flagged
        )

        analysis_duration = time.time() - start_time
        
        # Calculate duration of the video
        duration = target_fp.duration_seconds if target_fp else 0.0

        logger.info(
            "Media forensics pipeline complete",
            extra={
                "video_path": video_path,
                "composite_risk_score": risk_res.risk_score,
                "risk_level": risk_res.risk_level.value,
                "duration_seconds": round(analysis_duration, 2)
            }
        )

        return ForensicAnalysis(
            video_path=video_path,
            duration_seconds=round(duration, 2),
            fingerprint=target_fp,
            similarity_score=highest_similarity,
            matched_video_path=matched_path,
            deepfake=deepfake_res,
            watermark=watermark_res,
            metadata=metadata_res,
            ocr=ocr_result,
            logo=logo_result,
            risk=risk_res,
            analysis_duration_seconds=round(analysis_duration, 2)
        )
