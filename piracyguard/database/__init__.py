"""Database models for AI-PiracyGuard.

Re-exports all ORM models and enums for convenient access.
"""

from piracyguard.database.models import (
    Base,
    User,
    UserRole,
    Fingerprint,
    ScanJob,
    ScanResult,
    JobStatus,
    RiskLevel,
    Report,
    AuditLog,
    AuditAction,
)
from piracyguard.database.session import (
    get_engine,
    get_session,
    init_database,
)

__all__ = [
    "Base",
    "User",
    "UserRole",
    "Fingerprint",
    "ScanJob",
    "ScanResult",
    "JobStatus",
    "RiskLevel",
    "Report",
    "AuditLog",
    "AuditAction",
    "get_engine",
    "get_session",
    "init_database",
]
