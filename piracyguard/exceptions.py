"""Custom exception hierarchy for AI-PiracyGuard.

All application-specific exceptions inherit from PiracyGuardError.
This enables structured error handling with appropriate HTTP status
codes and machine-readable error codes for the API layer.
"""

from typing import Any, Dict, Optional


class PiracyGuardError(Exception):
    """Base exception for all AI-PiracyGuard errors.

    Attributes:
        message: Human-readable error description.
        error_code: Machine-readable error code (e.g., 'AUTH_TOKEN_EXPIRED').
        status_code: HTTP status code for API responses.
        details: Optional additional context for debugging.
    """

    def __init__(
        self,
        message: str = "An internal error occurred.",
        error_code: str = "INTERNAL_ERROR",
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.details = details or {}

    def to_dict(self) -> Dict[str, Any]:
        """Serialize exception for JSON API responses."""
        result: Dict[str, Any] = {
            "error": self.error_code,
            "message": self.message,
        }
        if self.details:
            result["details"] = self.details
        return result


# ── Authentication Errors ────────────────────────────────────────────

class AuthenticationError(PiracyGuardError):
    """Raised when authentication fails."""

    def __init__(
        self,
        message: str = "Authentication failed.",
        error_code: str = "AUTH_FAILED",
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(
            message=message,
            error_code=error_code,
            status_code=401,
            details=details,
        )


class TokenExpiredError(AuthenticationError):
    """Raised when a JWT token has expired."""

    def __init__(self) -> None:
        super().__init__(
            message="Access token has expired. Please refresh or re-authenticate.",
            error_code="AUTH_TOKEN_EXPIRED",
        )


class TokenInvalidError(AuthenticationError):
    """Raised when a JWT token is malformed or tampered with."""

    def __init__(self) -> None:
        super().__init__(
            message="Invalid or malformed token.",
            error_code="AUTH_TOKEN_INVALID",
        )


class TokenMissingError(AuthenticationError):
    """Raised when no JWT token is provided."""

    def __init__(self) -> None:
        super().__init__(
            message="Authorization token is required.",
            error_code="AUTH_TOKEN_MISSING",
        )


class InsufficientPermissionsError(PiracyGuardError):
    """Raised when the user lacks required permissions."""

    def __init__(
        self,
        required_role: str = "admin",
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(
            message=f"Insufficient permissions. Required role: {required_role}.",
            error_code="AUTH_INSUFFICIENT_PERMISSIONS",
            status_code=403,
            details=details,
        )


# ── Validation Errors ────────────────────────────────────────────────

class ValidationError(PiracyGuardError):
    """Raised when input data fails validation."""

    def __init__(
        self,
        message: str = "Input validation failed.",
        error_code: str = "VALIDATION_ERROR",
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(
            message=message,
            error_code=error_code,
            status_code=422,
            details=details,
        )


class FileValidationError(ValidationError):
    """Raised when an uploaded file fails validation."""

    def __init__(
        self,
        message: str = "File validation failed.",
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(
            message=message,
            error_code="FILE_VALIDATION_ERROR",
            details=details,
        )


class UnsupportedVideoFormatError(FileValidationError):
    """Raised when a video file has an unsupported format."""

    def __init__(self, filename: str, supported_formats: list) -> None:
        super().__init__(
            message=f"Unsupported video format: {filename}",
            details={
                "filename": filename,
                "supported_formats": supported_formats,
            },
        )


class FileTooLargeError(FileValidationError):
    """Raised when an uploaded file exceeds the size limit."""

    def __init__(self, size_mb: float, max_size_mb: int) -> None:
        super().__init__(
            message=f"File size ({size_mb:.1f}MB) exceeds maximum allowed ({max_size_mb}MB).",
            details={
                "size_mb": size_mb,
                "max_size_mb": max_size_mb,
            },
        )


# ── Resource Errors ──────────────────────────────────────────────────

class ResourceNotFoundError(PiracyGuardError):
    """Raised when a requested resource doesn't exist."""

    def __init__(
        self,
        resource_type: str = "resource",
        resource_id: str = "",
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(
            message=f"{resource_type} not found: {resource_id}" if resource_id else f"{resource_type} not found.",
            error_code="RESOURCE_NOT_FOUND",
            status_code=404,
            details=details,
        )


class VideoNotFoundError(ResourceNotFoundError):
    """Raised when a video file cannot be found."""

    def __init__(self, video_path: str) -> None:
        super().__init__(
            resource_type="Video",
            resource_id=video_path,
        )


class JobNotFoundError(ResourceNotFoundError):
    """Raised when a scan job cannot be found."""

    def __init__(self, job_id: str) -> None:
        super().__init__(
            resource_type="Job",
            resource_id=job_id,
        )


class ReportNotFoundError(ResourceNotFoundError):
    """Raised when a report cannot be found."""

    def __init__(self, report_id: str) -> None:
        super().__init__(
            resource_type="Report",
            resource_id=report_id,
        )


# ── Processing Errors ────────────────────────────────────────────────

class ProcessingError(PiracyGuardError):
    """Raised when video/media processing fails."""

    def __init__(
        self,
        message: str = "Media processing failed.",
        error_code: str = "PROCESSING_ERROR",
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(
            message=message,
            error_code=error_code,
            status_code=500,
            details=details,
        )


class FrameExtractionError(ProcessingError):
    """Raised when frame extraction from a video fails."""

    def __init__(self, video_path: str, reason: str = "") -> None:
        super().__init__(
            message=f"Failed to extract frames from: {video_path}. {reason}".strip(),
            error_code="FRAME_EXTRACTION_ERROR",
            details={"video_path": video_path},
        )


class FingerprintGenerationError(ProcessingError):
    """Raised when fingerprint generation fails."""

    def __init__(self, video_path: str, reason: str = "") -> None:
        super().__init__(
            message=f"Failed to generate fingerprint for: {video_path}. {reason}".strip(),
            error_code="FINGERPRINT_ERROR",
            details={"video_path": video_path},
        )


class ModelInferenceError(ProcessingError):
    """Raised when ML model inference fails."""

    def __init__(self, model_name: str, reason: str = "") -> None:
        super().__init__(
            message=f"Model inference failed for: {model_name}. {reason}".strip(),
            error_code="MODEL_INFERENCE_ERROR",
            details={"model_name": model_name},
        )


class ModelLoadError(ProcessingError):
    """Raised when an ML model fails to load."""

    def __init__(self, model_name: str, reason: str = "") -> None:
        super().__init__(
            message=f"Failed to load model: {model_name}. {reason}".strip(),
            error_code="MODEL_LOAD_ERROR",
            details={"model_name": model_name},
        )


# ── Database Errors ──────────────────────────────────────────────────

class DatabaseError(PiracyGuardError):
    """Raised when a database operation fails."""

    def __init__(
        self,
        message: str = "Database operation failed.",
        error_code: str = "DATABASE_ERROR",
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(
            message=message,
            error_code=error_code,
            status_code=500,
            details=details,
        )


class DuplicateEntryError(DatabaseError):
    """Raised when attempting to insert a duplicate record."""

    def __init__(self, resource_type: str, identifier: str) -> None:
        super().__init__(
            message=f"Duplicate {resource_type}: {identifier}",
            error_code="DUPLICATE_ENTRY",
            details={
                "resource_type": resource_type,
                "identifier": identifier,
            },
        )


# ── Rate Limiting ────────────────────────────────────────────────────

class RateLimitExceededError(PiracyGuardError):
    """Raised when API rate limit is exceeded."""

    def __init__(self, retry_after: int = 60) -> None:
        super().__init__(
            message=f"Rate limit exceeded. Retry after {retry_after} seconds.",
            error_code="RATE_LIMIT_EXCEEDED",
            status_code=429,
            details={"retry_after": retry_after},
        )
