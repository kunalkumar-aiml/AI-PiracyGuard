# Database package initializer for AI-PiracyGuard
from .db_manager import (
    init_db,
    save_fingerprint,
    get_all_fingerprints,
    save_scan_history,
    get_scan_history,
    get_db_stats,
)

__all__ = [
    "init_db",
    "save_fingerprint",
    "get_all_fingerprints",
    "save_scan_history",
    "get_scan_history",
    "get_db_stats",
]
