"""Unit test for forensic PDF report generation."""

import os
import tempfile
from datetime import datetime, timezone

from piracyguard.database.models import ScanJob, ScanResult, JobStatus, RiskLevel
from piracyguard.services.report_service import ReportService


def test_pdf_report_generation():
    # 1. Create mock database entities
    job = ScanJob(
        uuid="test-job-uuid-12345",
        status=JobStatus.COMPLETED,
        total_files=2,
        processed_files=2,
        started_at=datetime.now(timezone.utc),
        completed_at=datetime.now(timezone.utc),
        duration_seconds=1.85
    )

    results = [
        ScanResult(
            video_path="/path/to/movie_leak_cam.mp4",
            similarity_score=95.4,
            deepfake_score=15.0,
            watermark_present_score=80.0,
            risk_score=91.2,
            risk_level=RiskLevel.CRITICAL
        ),
        ScanResult(
            video_path="/path/to/interview_deepfake.mp4",
            similarity_score=0.0,
            deepfake_score=88.5,
            watermark_present_score=0.0,
            risk_score=76.8,
            risk_level=RiskLevel.HIGH
        )
    ]

    # 2. Setup destination file in temporary directory
    tmp_dir = tempfile.mkdtemp()
    dest_pdf = os.path.join(tmp_dir, "test_report.pdf")

    # 3. Call PDF generation service
    path = ReportService.generate_pdf_report(job, results, dest_pdf)

    # 4. Assertions
    assert path == dest_pdf
    assert os.path.exists(dest_pdf)
    assert os.path.getsize(dest_pdf) > 0
    
    print(f"[+] PDF Report successfully generated at: {dest_pdf}")
