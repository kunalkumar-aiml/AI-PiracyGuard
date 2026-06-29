"""Forensic scanning endpoints blueprint for AI-PiracyGuard API.

Enqueues background video scans, registers reference files, and tracks status.
"""

from flask import Blueprint, request, jsonify, g

from piracyguard.config import settings
from piracyguard.database.session import session_scope
from piracyguard.api.middleware.auth import token_required, role_required
from piracyguard.services.job_service import JobService
from piracyguard.services.scan_service import ScanService
from piracyguard.exceptions import ValidationError
from piracyguard.logging_config import get_logger

logger = get_logger(__name__)

scans_bp = Blueprint("scans", __name__)
job_service = JobService()
scan_service = ScanService()


@scans_bp.route("/run", methods=["POST"])
@token_required
def run_scan() -> tuple:
    """Enqueue scan job for all videos in upload directory.

    Endpoint: POST /api/v1/scans/run
    """
    user_id = g.current_user.get("id")
    
    # Target folder is read from settings (default: uploads)
    # Ensure directory is created
    settings.ensure_directories()
    upload_folder = str(settings.BASE_DIR / settings.UPLOAD_DIR)

    with session_scope() as db:
        job_uuid = job_service.start_scan_job(db, upload_folder, user_id=user_id)

    return jsonify({
        "message": "Scan job enqueued successfully.",
        "job_id": job_uuid
    }), 202


@scans_bp.route("/job/<job_uuid>", methods=["GET"])
@token_required
def get_job_status(job_uuid: str) -> tuple:
    """Retrieve status, progress, and results of a scan job.

    Endpoint: GET /api/v1/scans/job/<job_uuid>
    """
    with session_scope() as db:
        status_data = job_service.get_job_status(db, job_uuid)

    if status_data.get("status") == "not_found":
        return jsonify({"error": "Scan job not found."}), 404

    return jsonify(status_data), 200


@scans_bp.route("/register", methods=["POST"])
@token_required
@role_required("admin", "analyst")
def register_reference() -> tuple:
    """Generate and register fingerprint for a known reference video.

    Endpoint: POST /api/v1/scans/register
    Request payload: { "video_path": "/path/to/original.mp4" }
    """
    data = request.get_json()
    if not data or "video_path" not in data:
        raise ValidationError("video_path is a required field.")

    video_path = data["video_path"]
    user_id = g.current_user.get("id")

    with session_scope() as db:
        # Register reference fingerprint
        db_fp = scan_service.register_reference_video(db, video_path, user_id=user_id)
        
    return jsonify({
        "message": "Reference video registered successfully.",
        "uuid": db_fp.uuid,
        "video_path": db_fp.video_path
    }), 201
