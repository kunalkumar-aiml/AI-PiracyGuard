"""Compatibility configuration redirect.

Redirects attributes to the new central piracyguard.config.settings container.
"""

from piracyguard.config import settings

# Expose key settings as module attributes for backward compatibility
SCAN_FOLDER = str(settings.UPLOAD_DIR)
REPORT_FILE = str(settings.REPORT_DIR / "scan_report.txt")
LOG_FILE = str(settings.LOG_DIR / "activity_log.txt")

PIRACY_THRESHOLD = settings.PIRACY_THRESHOLD
DEEPFAKE_THRESHOLD = settings.DEEPFAKE_THRESHOLD
