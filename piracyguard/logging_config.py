"""Structured logging configuration for AI-PiracyGuard.

Provides JSON-formatted structured logging in production and
human-readable colored output in development.

Usage:
    from piracyguard.logging_config import get_logger
    logger = get_logger(__name__)
    logger.info("Scan started", extra={"video_path": path, "job_id": job_id})
"""

import logging
import logging.handlers
import json
import sys
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional


class JSONFormatter(logging.Formatter):
    """Structured JSON log formatter for production environments.

    Outputs one JSON object per line, suitable for log aggregation
    tools like ELK, Datadog, or CloudWatch.
    """

    def format(self, record: logging.LogRecord) -> str:
        log_entry: Dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Include extra fields (e.g., job_id, video_path)
        for key in ("video_path", "job_id", "user", "scan_id", "duration",
                     "model_name", "risk_score", "error_code", "request_id"):
            value = getattr(record, key, None)
            if value is not None:
                log_entry[key] = value

        # Include exception info
        if record.exc_info and record.exc_info[1]:
            log_entry["exception"] = {
                "type": type(record.exc_info[1]).__name__,
                "message": str(record.exc_info[1]),
            }

        return json.dumps(log_entry, default=str)


class ColoredFormatter(logging.Formatter):
    """Colored console formatter for development environments."""

    COLORS = {
        "DEBUG": "\033[36m",      # Cyan
        "INFO": "\033[32m",       # Green
        "WARNING": "\033[33m",    # Yellow
        "ERROR": "\033[31m",      # Red
        "CRITICAL": "\033[1;31m", # Bold Red
    }
    RESET = "\033[0m"

    def format(self, record: logging.LogRecord) -> str:
        color = self.COLORS.get(record.levelname, self.RESET)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        base = f"{color}[{timestamp}] {record.levelname:8s}{self.RESET} {record.name}: {record.getMessage()}"

        # Append extra context fields if present
        extras = []
        for key in ("video_path", "job_id", "user", "scan_id", "duration",
                     "model_name", "risk_score"):
            value = getattr(record, key, None)
            if value is not None:
                extras.append(f"{key}={value}")

        if extras:
            base += f" | {', '.join(extras)}"

        if record.exc_info and record.exc_info[1]:
            base += f"\n  └─ {type(record.exc_info[1]).__name__}: {record.exc_info[1]}"

        return base


def setup_logging(
    level: str = "INFO",
    log_dir: Optional[str] = None,
    json_format: bool = False,
) -> None:
    """Configure the root logger for the application.

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
        log_dir: Directory for log files. If None, logs only to console.
        json_format: Use JSON formatting (recommended for production).
    """
    root_logger = logging.getLogger("piracyguard")
    root_logger.setLevel(getattr(logging, level.upper(), logging.INFO))

    # Clear existing handlers to avoid duplicate log entries
    root_logger.handlers.clear()

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    if json_format:
        console_handler.setFormatter(JSONFormatter())
    else:
        console_handler.setFormatter(ColoredFormatter())
    root_logger.addHandler(console_handler)

    # File handler (rotating, 10MB max, keep 5 backups)
    if log_dir:
        log_path = Path(log_dir)
        log_path.mkdir(parents=True, exist_ok=True)

        file_handler = logging.handlers.RotatingFileHandler(
            filename=log_path / "piracyguard.log",
            maxBytes=10 * 1024 * 1024,  # 10 MB
            backupCount=5,
            encoding="utf-8",
        )
        file_handler.setFormatter(JSONFormatter())
        root_logger.addHandler(file_handler)

        # Separate error log file
        error_handler = logging.handlers.RotatingFileHandler(
            filename=log_path / "piracyguard_errors.log",
            maxBytes=10 * 1024 * 1024,
            backupCount=5,
            encoding="utf-8",
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(JSONFormatter())
        root_logger.addHandler(error_handler)

    # Reduce noise from third-party libraries
    for noisy_logger in ("urllib3", "PIL", "werkzeug", "sqlalchemy.engine"):
        logging.getLogger(noisy_logger).setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Get a child logger under the piracyguard namespace.

    Args:
        name: Logger name (typically __name__).

    Returns:
        Configured logger instance.

    Usage:
        logger = get_logger(__name__)
        logger.info("Processing video", extra={"video_path": "/path/to/video.mp4"})
    """
    if name.startswith("piracyguard."):
        return logging.getLogger(name)
    return logging.getLogger(f"piracyguard.{name}")
