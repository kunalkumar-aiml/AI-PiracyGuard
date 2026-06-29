"""Forensic reporting endpoints blueprint for AI-PiracyGuard API.

Triggers report compilation and serves PDF document downloads.
"""

import os
from flask import Blueprint, request, jsonify, send_file, g

from piracyguard.config import settings
from piracyguard.database.session import session_scope
from piracyguard.database.models import ScanJob, ScanResult, Report
from piracyguard.api.middleware.auth import token_required
from piracyguard.services.report_service import ReportService
from piracyguard.exceptions import ValidationError, ResourceNotFoundError
from piracyguard.logging_config import get_logger

logger = get_logger(__name__)

reports_bp = Blueprint("reports", __name__)
report_service = ReportService()


@reports_bp.route("/job/<job_uuid>", methods=["POST"])
@token_required
def generate_report(job_uuid: str) -> tuple:
    """Generate a PDF forensic report for a completed scan job.

    Endpoint: POST /api/v1/reports/job/<job_uuid>
    """
    user_id = g.current_user.get("id")

    with session_scope() as db:
        # Query job
        job = db.query(ScanJob).filter(ScanJob.uuid == job_uuid).first()
        if not job:
            raise ResourceNotFoundError("ScanJob", job_uuid)

        # Ensure job is completed
        if job.status.value != "completed":
            raise ValidationError(
                f"Cannot generate report for job in status: {job.status.value}."
            )

        # Query scan results
        results = db.query(ScanResult).filter(ScanResult.job_id == job.id).all()

        # Define destination file path
        report_filename = f"forensic_report_{job_uuid}.pdf"
        dest_path = str(settings.BASE_DIR / settings.REPORT_DIR / report_filename)

        # Generate report
        report_service.generate_pdf_report(job, results, dest_path)

        # Create or update report record
        report = db.query(Report).filter(Report.job_id == job.id).first()
        if not report:
            report = Report(
                job_id=job.id,
                report_type="pdf",
                file_path=dest_path,
                generated_by=user_id
            )
            db.add(report)
            db.commit()
            db.refresh(report)

        report_uuid = report.uuid

    # Return download URL path
    download_url = f"/api/v1/reports/download/{report_uuid}"

    return jsonify({
        "message": "Report generated successfully.",
        "report_id": report_uuid,
        "download_url": download_url
    }), 201


@reports_bp.route("/download/<report_uuid>", methods=["GET"])
def download_report(report_uuid: str):
    """Download a generated PDF report file.

    Endpoint: GET /api/v1/reports/download/<report_uuid>
    Note: Open access download link (auth verified during token generation)
    """
    with session_scope() as db:
        report = db.query(Report).filter(Report.uuid == report_uuid).first()
        if not report:
            raise ResourceNotFoundError("Report", report_uuid)

        file_path = report.file_path

    if not os.path.exists(file_path):
        raise ResourceNotFoundError("Report file", report_uuid)

    logger.info("Serving report file download", extra={"report_uuid": report_uuid, "file_path": file_path})

    return send_file(
        file_path,
        mimetype="application/pdf",
        as_attachment=True,
        download_name=os.path.basename(file_path)
    )
