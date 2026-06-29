"""Background task worker and scan job service.

Uses thread/process execution pool to manage asynchronous forensics processing.
Saves job states in database, preventing external broker dependencies.
"""

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import os
import time
from typing import Dict, Any, List, Optional
import uuid

from sqlalchemy.orm import Session

from piracyguard.config import settings
from piracyguard.database.session import session_scope, get_session
from piracyguard.database.models import ScanJob, ScanResult, JobStatus, User
from piracyguard.services.scan_service import ScanService
from piracyguard.logging_config import get_logger

logger = get_logger(__name__)

# Single global thread executor for the worker pool
# Max workers matches settings or defaults to 2 (to keep CPU usage reasonable on Macs)
_executor = ThreadPoolExecutor(max_workers=max(1, settings.MAX_CONCURRENT_SCANS))


class JobService:
    """Manages background forensic scanning jobs using thread pool."""

    def __init__(self, scan_service: Optional[ScanService] = None) -> None:
        self.scan_service = scan_service or ScanService()

    def create_job(self, db: Session, user_id: Optional[int] = None) -> ScanJob:
        """Create and commit a new pending scan job.

        Args:
            db: Database session.
            user_id: ID of the user triggering the scan.

        Returns:
            ScanJob ORM object.
        """
        job = ScanJob(
            status=JobStatus.PENDING,
            user_id=user_id
        )
        db.add(job)
        db.commit()
        db.refresh(job)
        logger.info("Created background scan job", extra={"job_uuid": job.uuid})
        return job

    def start_scan_job(self, db: Session, upload_folder: str, user_id: Optional[int] = None) -> str:
        """Enqueue scanning of all videos in the upload folder.

        Creates a job database record and submits a future task to the ThreadPoolExecutor.

        Args:
            db: Database session.
            upload_folder: Path to folder containing uploads.
            user_id: Triggering user ID.

        Returns:
            String UUID of the enqueued job.
        """
        # Create DB record
        job = self.create_job(db, user_id=user_id)

        # Submit task to ThreadPoolExecutor
        _executor.submit(self._run_job_wrapper, job.id, upload_folder)

        return job.uuid

    def _run_job_wrapper(self, job_row_id: int, upload_folder: str) -> None:
        """Wrapper method that runs in background thread.

        Establishes its own database session using context manager.
        """
        start_time = time.time()
        logger.info("Background thread starting job execution", extra={"job_id": job_row_id})

        with session_scope() as db:
            # Load job row
            job = db.query(ScanJob).filter(ScanJob.id == job_row_id).first()
            if not job:
                logger.error(f"Job not found in database: ID {job_row_id}")
                return

            job.status = JobStatus.RUNNING
            job.started_at = datetime.now(timezone.utc)
            db.commit()

            try:
                # Find all supported files in upload directory
                if not os.path.exists(upload_folder):
                    raise FileNotFoundError(f"Scan directory not found: {upload_folder}")

                supported_exts = tuple(settings.SUPPORTED_VIDEO_FORMATS)
                files = [
                    os.path.join(upload_folder, f)
                    for f in os.listdir(upload_folder)
                    if f.lower().endswith(supported_exts)
                ]

                job.total_files = len(files)
                db.commit()

                if not files:
                    logger.info("No video files found in scan directory")
                    job.status = JobStatus.COMPLETED
                    job.completed_at = datetime.now(timezone.utc)
                    job.duration_seconds = round(time.time() - start_time, 2)
                    db.commit()
                    return

                # Process each file
                processed_count = 0
                for video_path in files:
                    try:
                        self.scan_service.scan_video(db, video_path, job.id)
                    except Exception as e:
                        logger.error(
                            f"Error processing video {video_path}: {e}",
                            exc_info=True
                        )
                        # We continue processing other files in the folder
                    
                    processed_count += 1
                    job.processed_files = processed_count
                    db.commit()

                # Mark complete
                job.status = JobStatus.COMPLETED
                job.completed_at = datetime.now(timezone.utc)
                job.duration_seconds = round(time.time() - start_time, 2)
                db.commit()

                logger.info(
                    "Background job completed successfully",
                    extra={"job_uuid": job.uuid, "processed_files": processed_count}
                )

            except Exception as e:
                logger.error(f"Background job execution failed: {e}", exc_info=True)
                job.status = JobStatus.FAILED
                job.error_message = str(e)
                job.completed_at = datetime.now(timezone.utc)
                job.duration_seconds = round(time.time() - start_time, 2)
                db.commit()

    def get_job_status(self, db: Session, job_uuid: str) -> Dict[str, Any]:
        """Query status and details of a background job.

        Args:
            db: Database session.
            job_uuid: String UUID of job.

        Returns:
            Dict containing status, progress, duration, results list.
        """
        job = db.query(ScanJob).filter(ScanJob.uuid == job_uuid).first()
        if not job:
            return {"status": "not_found"}

        results = []
        # Get results if completed or running
        db_results = db.query(ScanResult).filter(ScanResult.job_id == job.id).all()
        for r in db_results:
            results.append({
                "video_path": r.video_path,
                "risk_score": r.risk_score,
                "risk_level": r.risk_level.value if r.risk_level else None,
                "similarity": r.similarity_score,
                "deepfake_score": r.deepfake_score,
                "recommended_action": r.recommended_action
            })

        return {
            "uuid": job.uuid,
            "status": job.status.value,
            "total_files": job.total_files,
            "processed_files": job.processed_files,
            "progress_percent": job.progress_percent,
            "error_message": job.error_message,
            "started_at": job.started_at.isoformat() if job.started_at else None,
            "completed_at": job.completed_at.isoformat() if job.completed_at else None,
            "duration_seconds": job.duration_seconds,
            "results": results
        }
