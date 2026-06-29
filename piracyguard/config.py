"""Centralized configuration management for AI-PiracyGuard.

Uses environment variables with sensible defaults for development.
Production deployments MUST set all required environment variables.

Usage:
    from piracyguard.config import settings
    print(settings.SECRET_KEY)
"""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


def _get_bool(key: str, default: bool = False) -> bool:
    """Read a boolean from environment variables."""
    val = os.environ.get(key, str(default)).lower()
    return val in ("true", "1", "yes", "on")


def _get_int(key: str, default: int = 0) -> int:
    """Read an integer from environment variables."""
    try:
        return int(os.environ.get(key, str(default)))
    except (ValueError, TypeError):
        return default


def _get_list(key: str, default: str = "") -> List[str]:
    """Read a comma-separated list from environment variables."""
    val = os.environ.get(key, default)
    if not val:
        return []
    return [item.strip() for item in val.split(",") if item.strip()]


@dataclass(frozen=True)
class Settings:
    """Application-wide configuration container.

    All settings are read once at import time from environment variables.
    The frozen dataclass ensures immutability after initialization.
    """

    # ── Application ──────────────────────────────────────────────────
    APP_NAME: str = "AI Piracy Guard"
    APP_VERSION: str = "2.0.0"
    ENVIRONMENT: str = field(
        default_factory=lambda: os.environ.get("APP_ENV", "development")
    )
    DEBUG: bool = field(
        default_factory=lambda: _get_bool("FLASK_DEBUG", False)
    )
    LOG_LEVEL: str = field(
        default_factory=lambda: os.environ.get("LOG_LEVEL", "INFO")
    )

    # ── Security ─────────────────────────────────────────────────────
    SECRET_KEY: str = field(
        default_factory=lambda: os.environ.get(
            "SECRET_KEY", "change-me-in-production-" + os.urandom(8).hex()
        )
    )
    JWT_ACCESS_TOKEN_EXPIRES_MINUTES: int = field(
        default_factory=lambda: _get_int("JWT_ACCESS_TOKEN_EXPIRES_MINUTES", 120)
    )
    JWT_REFRESH_TOKEN_EXPIRES_DAYS: int = field(
        default_factory=lambda: _get_int("JWT_REFRESH_TOKEN_EXPIRES_DAYS", 30)
    )
    JWT_ALGORITHM: str = "HS256"

    # ── Authentication ───────────────────────────────────────────────
    ADMIN_USERNAME: str = field(
        default_factory=lambda: os.environ.get("ADMIN_USERNAME", "admin")
    )
    ADMIN_PASSWORD_HASH: str = field(
        default_factory=lambda: os.environ.get("ADMIN_PASSWORD_HASH", "")
    )
    BCRYPT_ROUNDS: int = field(
        default_factory=lambda: _get_int("BCRYPT_ROUNDS", 12)
    )

    # ── Paths ────────────────────────────────────────────────────────
    BASE_DIR: Path = field(
        default_factory=lambda: Path(
            os.environ.get("BASE_DIR", str(Path(__file__).resolve().parent.parent))
        )
    )
    UPLOAD_DIR: Path = field(
        default_factory=lambda: Path(
            os.environ.get("UPLOAD_DIR", "uploads")
        )
    )
    REPORT_DIR: Path = field(
        default_factory=lambda: Path(
            os.environ.get("REPORT_DIR", "reports")
        )
    )
    LOG_DIR: Path = field(
        default_factory=lambda: Path(
            os.environ.get("LOG_DIR", "logs")
        )
    )
    MODEL_DIR: Path = field(
        default_factory=lambda: Path(
            os.environ.get("MODEL_DIR", "models/weights")
        )
    )

    # ── Database ─────────────────────────────────────────────────────
    DATABASE_URL: str = field(
        default_factory=lambda: os.environ.get(
            "DATABASE_URL", "sqlite:///database/piracyguard.db"
        )
    )

    # ── Detection Thresholds ─────────────────────────────────────────
    PIRACY_THRESHOLD: float = field(
        default_factory=lambda: float(
            os.environ.get("PIRACY_THRESHOLD", "75.0")
        )
    )
    DEEPFAKE_THRESHOLD: float = field(
        default_factory=lambda: float(
            os.environ.get("DEEPFAKE_THRESHOLD", "60.0")
        )
    )
    WATERMARK_THRESHOLD: float = field(
        default_factory=lambda: float(
            os.environ.get("WATERMARK_THRESHOLD", "50.0")
        )
    )

    # ── Risk Engine Weights ──────────────────────────────────────────
    RISK_WEIGHT_SIMILARITY: float = field(
        default_factory=lambda: float(
            os.environ.get("RISK_WEIGHT_SIMILARITY", "0.30")
        )
    )
    RISK_WEIGHT_DEEPFAKE: float = field(
        default_factory=lambda: float(
            os.environ.get("RISK_WEIGHT_DEEPFAKE", "0.25")
        )
    )
    RISK_WEIGHT_WATERMARK: float = field(
        default_factory=lambda: float(
            os.environ.get("RISK_WEIGHT_WATERMARK", "0.15")
        )
    )
    RISK_WEIGHT_METADATA: float = field(
        default_factory=lambda: float(
            os.environ.get("RISK_WEIGHT_METADATA", "0.15")
        )
    )
    RISK_WEIGHT_AUDIO: float = field(
        default_factory=lambda: float(
            os.environ.get("RISK_WEIGHT_AUDIO", "0.10")
        )
    )
    RISK_WEIGHT_FRAME_CONSISTENCY: float = field(
        default_factory=lambda: float(
            os.environ.get("RISK_WEIGHT_FRAME_CONSISTENCY", "0.05")
        )
    )

    # ── Video Processing ─────────────────────────────────────────────
    FRAME_SAMPLE_STEP: int = field(
        default_factory=lambda: _get_int("FRAME_SAMPLE_STEP", 30)
    )
    MAX_FRAMES_PER_VIDEO: int = field(
        default_factory=lambda: _get_int("MAX_FRAMES_PER_VIDEO", 100)
    )
    SUPPORTED_VIDEO_FORMATS: List[str] = field(
        default_factory=lambda: _get_list(
            "SUPPORTED_VIDEO_FORMATS",
            ".mp4,.avi,.mkv,.mov,.webm,.flv,.wmv"
        )
    )
    MAX_UPLOAD_SIZE_MB: int = field(
        default_factory=lambda: _get_int("MAX_UPLOAD_SIZE_MB", 500)
    )

    # ── ML Models ────────────────────────────────────────────────────
    DEEPFAKE_MODEL_NAME: str = field(
        default_factory=lambda: os.environ.get(
            "DEEPFAKE_MODEL_NAME", "efficientnet-b4"
        )
    )
    DEEPFAKE_BATCH_SIZE: int = field(
        default_factory=lambda: _get_int("DEEPFAKE_BATCH_SIZE", 8)
    )
    USE_GPU: bool = field(
        default_factory=lambda: _get_bool("USE_GPU", False)
    )

    # ── API ──────────────────────────────────────────────────────────
    API_VERSION: str = "v1"
    RATE_LIMIT_DEFAULT: str = field(
        default_factory=lambda: os.environ.get("RATE_LIMIT_DEFAULT", "100/hour")
    )
    CORS_ORIGINS: List[str] = field(
        default_factory=lambda: _get_list(
            "CORS_ORIGINS", "http://localhost:3000,http://localhost:5173"
        )
    )

    # ── Workers ──────────────────────────────────────────────────────
    CELERY_BROKER_URL: str = field(
        default_factory=lambda: os.environ.get(
            "CELERY_BROKER_URL", "redis://localhost:6379/0"
        )
    )
    CELERY_RESULT_BACKEND: str = field(
        default_factory=lambda: os.environ.get(
            "CELERY_RESULT_BACKEND", "redis://localhost:6379/0"
        )
    )
    MAX_CONCURRENT_SCANS: int = field(
        default_factory=lambda: _get_int("MAX_CONCURRENT_SCANS", 4)
    )

    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.ENVIRONMENT.lower() == "production"

    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.ENVIRONMENT.lower() == "development"

    def ensure_directories(self) -> None:
        """Create required directories if they don't exist."""
        for dir_path in [self.UPLOAD_DIR, self.REPORT_DIR, self.LOG_DIR, self.MODEL_DIR]:
            resolved = self.BASE_DIR / dir_path if not dir_path.is_absolute() else dir_path
            resolved.mkdir(parents=True, exist_ok=True)


# Singleton instance — import this everywhere
settings = Settings()
