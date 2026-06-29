"""Flask Application Factory for AI-PiracyGuard.

Initializes configuration, sets up structured logging, establishes database connection,
configures CORS, registers blueprints, and hooks global error handling.
"""

import os
from typing import Optional

from flask import Flask, jsonify

from piracyguard.config import settings
from piracyguard.database.session import init_database
from piracyguard.api.middleware.error_handler import register_error_handlers
from piracyguard.logging_config import setup_logging, get_logger

# Import Blueprints
from piracyguard.api.routes.auth import auth_bp
from piracyguard.api.routes.scans import scans_bp
from piracyguard.api.routes.reports import reports_bp
from piracyguard.api.routes.analytics import analytics_bp

logger = get_logger(__name__)


def create_app(config_url: Optional[str] = None) -> Flask:
    """Create and configure the Flask application instance.

    Args:
        config_url: Database URL override.

    Returns:
        Configured Flask application.
    """
    # 1. Setup Structured Logging
    # JSON-formatted in production, colored/formatted in development
    setup_logging(
        level=settings.LOG_LEVEL,
        log_dir=str(settings.BASE_DIR / settings.LOG_DIR),
        json_format=settings.is_production
    )

    logger.info("Initializing Flask application", extra={"env": settings.ENVIRONMENT})

    # Create app instance
    app = Flask(__name__)

    # Load Flask settings
    app.config["SECRET_KEY"] = settings.SECRET_KEY
    app.config["MAX_CONTENT_LENGTH"] = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024

    # 2. Initialize Database Tables
    db_url = config_url or settings.DATABASE_URL
    try:
        init_database(db_url)
    except Exception as e:
        logger.critical(f"Database initialization failed: {e}", exc_info=True)
        # We don't crash app creation immediately if in testing context,
        # but in production, database failure is a hard stop.
        if settings.is_production:
            raise

    # 3. Enable CORS (Cross-Origin Resource Sharing)
    # Simple manual CORS headers middleware to avoid extra package dependency
    @app.after_request
    def apply_cors_headers(response):
        origins = ",".join(settings.CORS_ORIGINS)
        response.headers["Access-Control-Allow-Origin"] = origins
        response.headers["Access-Control-Allow-Headers"] = "Content-Type,Authorization"
        response.headers["Access-Control-Allow-Methods"] = "GET,POST,PUT,DELETE,OPTIONS"
        return response

    # Handle preflight OPTIONS requests
    @app.route("/<path:path>", methods=["OPTIONS"])
    def handle_options(path):
        return "", 204

    # 4. Hook Global Error Handling
    register_error_handlers(app)

    # 5. Register Blueprints (prefixed with API version)
    version_prefix = f"/api/{settings.API_VERSION}"
    
    app.register_blueprint(auth_bp, url_prefix=f"{version_prefix}/auth")
    app.register_blueprint(scans_bp, url_prefix=f"{version_prefix}/scans")
    app.register_blueprint(reports_bp, url_prefix=f"{version_prefix}/reports")
    app.register_blueprint(analytics_bp, url_prefix=f"{version_prefix}/analytics")

    # Core status endpoint
    @app.route("/")
    def status() -> tuple:
        return jsonify({
            "service": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "environment": settings.ENVIRONMENT,
            "status": "online"
        }), 200

    logger.info("Flask application configured and ready")
    return app


# Create default instance for WSGI servers (Gunicorn/uWSGI)
# Command: gunicorn "piracyguard.app:app"
app = create_app()
