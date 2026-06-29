"""Analytics endpoints blueprint for AI-PiracyGuard API.

Serves dashboard threat statistics and scan history trends.
"""

from flask import Blueprint, jsonify

from piracyguard.database.session import session_scope
from piracyguard.database.models import ScanResult
from piracyguard.api.middleware.auth import token_required
from piracyguard.services.scan_service import ScanService
from piracyguard.logging_config import get_logger

logger = get_logger(__name__)

analytics_bp = Blueprint("analytics", __name__)
scan_service = ScanService()


@analytics_bp.route("/stats", methods=["GET"])
@token_required
def get_stats() -> tuple:
    """Retrieve overview statistics for the main dashboard.

    Endpoint: GET /api/v1/analytics/stats
    """
    with session_scope() as db:
        stats_data = scan_service.get_stats(db)
    return jsonify(stats_data), 200


@analytics_bp.route("/history", methods=["GET"])
@token_required
def get_history() -> tuple:
    """Retrieve full list of forensic scan results.

    Endpoint: GET /api/v1/analytics/history
    """
    history = []
    with session_scope() as db:
        results = db.query(ScanResult).order_by(ScanResult.created_at.desc()).all()
        for r in results:
            history.append({
                "uuid": r.uuid,
                "video_path": r.video_path,
                "similarity": r.similarity_score,
                "deepfake_score": r.deepfake_score,
                "risk_score": r.risk_score,
                "risk_level": r.risk_level.value if r.risk_level else None,
                "scanned_at": r.created_at.isoformat()
            })

    return jsonify({"scan_history": history}), 200
