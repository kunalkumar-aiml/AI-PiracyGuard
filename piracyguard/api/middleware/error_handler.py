"""Global error handler middleware for AI-PiracyGuard API.

Catches all exceptions and returns structured JSON error responses.
Integrates with the custom exception hierarchy for consistent error codes.
"""

from flask import Flask, jsonify, Response
from werkzeug.exceptions import HTTPException

from piracyguard.exceptions import PiracyGuardError
from piracyguard.logging_config import get_logger

logger = get_logger(__name__)


def register_error_handlers(app: Flask) -> None:
    """Register global error handlers on the Flask application.

    Args:
        app: Flask application instance.
    """

    @app.errorhandler(PiracyGuardError)
    def handle_piracyguard_error(error: PiracyGuardError) -> tuple[Response, int]:
        """Handle all custom PiracyGuard exceptions."""
        logger.warning(
            f"{error.error_code}: {error.message}",
            extra={"error_code": error.error_code},
        )
        response = jsonify(error.to_dict())
        response.status_code = error.status_code
        return response, error.status_code

    @app.errorhandler(HTTPException)
    def handle_http_error(error: HTTPException) -> tuple[Response, int]:
        """Handle standard HTTP exceptions (404, 405, etc.)."""
        response = jsonify({
            "error": error.name.upper().replace(" ", "_"),
            "message": error.description,
        })
        return response, error.code or 500

    @app.errorhandler(404)
    def handle_not_found(error: HTTPException) -> tuple[Response, int]:
        """Handle 404 Not Found."""
        return jsonify({
            "error": "NOT_FOUND",
            "message": "The requested resource was not found.",
        }), 404

    @app.errorhandler(405)
    def handle_method_not_allowed(error: HTTPException) -> tuple[Response, int]:
        """Handle 405 Method Not Allowed."""
        return jsonify({
            "error": "METHOD_NOT_ALLOWED",
            "message": "The HTTP method is not allowed for this endpoint.",
        }), 405

    @app.errorhandler(413)
    def handle_payload_too_large(error: HTTPException) -> tuple[Response, int]:
        """Handle 413 Payload Too Large."""
        return jsonify({
            "error": "PAYLOAD_TOO_LARGE",
            "message": "The uploaded file exceeds the maximum allowed size.",
        }), 413

    @app.errorhandler(429)
    def handle_rate_limit(error: HTTPException) -> tuple[Response, int]:
        """Handle 429 Too Many Requests."""
        return jsonify({
            "error": "RATE_LIMIT_EXCEEDED",
            "message": "Too many requests. Please try again later.",
        }), 429

    @app.errorhandler(500)
    def handle_internal_error(error: Exception) -> tuple[Response, int]:
        """Handle unexpected 500 Internal Server Errors."""
        logger.error(
            f"Unhandled error: {error}",
            exc_info=True,
        )
        return jsonify({
            "error": "INTERNAL_ERROR",
            "message": "An unexpected error occurred. Please try again later.",
        }), 500

    @app.errorhandler(Exception)
    def handle_unexpected_error(error: Exception) -> tuple[Response, int]:
        """Catch-all for any unhandled exceptions."""
        # Re-raise PiracyGuardErrors to their own handler
        if isinstance(error, PiracyGuardError):
            return handle_piracyguard_error(error)

        logger.error(
            f"Unexpected error: {type(error).__name__}: {error}",
            exc_info=True,
        )
        return jsonify({
            "error": "INTERNAL_ERROR",
            "message": "An unexpected error occurred. Please try again later.",
        }), 500
