"""SQLAlchemy ORM models for AI-PiracyGuard.

Defines all database tables with proper relationships, indexes,
and audit fields. Supports SQLite (default) and PostgreSQL.
"""

import enum
import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import (
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    Boolean,
    JSON,
)
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    relationship,
)


class Base(DeclarativeBase):
    """Base class for all ORM models."""
    pass


def _utcnow() -> datetime:
    """Return current UTC timestamp."""
    return datetime.now(timezone.utc)


def _generate_uuid() -> str:
    """Generate a new UUID4 string."""
    return str(uuid.uuid4())


# ── Enums ────────────────────────────────────────────────────────────

class UserRole(str, enum.Enum):
    """User roles for RBAC."""
    ADMIN = "admin"
    ANALYST = "analyst"
    VIEWER = "viewer"


class RiskLevel(str, enum.Enum):
    """Risk classification levels."""
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    NONE = "NONE"


class JobStatus(str, enum.Enum):
    """Background job status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class AuditAction(str, enum.Enum):
    """Types of auditable actions."""
    LOGIN = "login"
    LOGOUT = "logout"
    SCAN_STARTED = "scan_started"
    SCAN_COMPLETED = "scan_completed"
    VIDEO_REGISTERED = "video_registered"
    REPORT_GENERATED = "report_generated"
    USER_CREATED = "user_created"
    USER_UPDATED = "user_updated"
    SETTINGS_CHANGED = "settings_changed"


# ── Models ───────────────────────────────────────────────────────────

class User(Base):
    """User accounts with RBAC support."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    uuid: Mapped[str] = mapped_column(
        String(36), unique=True, nullable=False, default=_generate_uuid
    )
    username: Mapped[str] = mapped_column(String(80), unique=True, nullable=False, index=True)
    email: Mapped[Optional[str]] = mapped_column(String(255), unique=True, nullable=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole), nullable=False, default=UserRole.VIEWER
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_login: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, onupdate=_utcnow, nullable=False
    )

    # Relationships
    scans: Mapped[list["ScanJob"]] = relationship(back_populates="user", lazy="dynamic")
    audit_logs: Mapped[list["AuditLog"]] = relationship(back_populates="user", lazy="dynamic")

    def __repr__(self) -> str:
        return f"<User {self.username} ({self.role.value})>"


class Fingerprint(Base):
    """Video fingerprint records for similarity matching."""

    __tablename__ = "fingerprints"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    uuid: Mapped[str] = mapped_column(
        String(36), unique=True, nullable=False, default=_generate_uuid
    )
    video_path: Mapped[str] = mapped_column(String(1024), unique=True, nullable=False)
    video_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
    fingerprint_ahash: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    fingerprint_phash: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    fingerprint_dhash: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    fingerprint_temporal: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    frame_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    duration_seconds: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    codec: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    resolution: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    fps: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    file_size_bytes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    metadata_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    registered_by: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, nullable=False
    )

    __table_args__ = (
        Index("idx_fingerprints_video_hash", "video_hash"),
        Index("idx_fingerprints_created_at", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<Fingerprint {self.video_path}>"


class ScanJob(Base):
    """Background scan job tracking."""

    __tablename__ = "scan_jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    uuid: Mapped[str] = mapped_column(
        String(36), unique=True, nullable=False, default=_generate_uuid, index=True
    )
    status: Mapped[JobStatus] = mapped_column(
        Enum(JobStatus), nullable=False, default=JobStatus.PENDING
    )
    total_files: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    processed_files: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    started_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    duration_seconds: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    user_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, nullable=False
    )

    # Relationships
    user: Mapped[Optional["User"]] = relationship(back_populates="scans")
    results: Mapped[list["ScanResult"]] = relationship(
        back_populates="job", lazy="dynamic", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("idx_scan_jobs_status", "status"),
        Index("idx_scan_jobs_created_at", "created_at"),
    )

    @property
    def progress_percent(self) -> float:
        """Calculate scan progress as a percentage."""
        if self.total_files == 0:
            return 0.0
        return round((self.processed_files / self.total_files) * 100, 1)

    def __repr__(self) -> str:
        return f"<ScanJob {self.uuid} ({self.status.value})>"


class ScanResult(Base):
    """Individual scan results for each video analyzed."""

    __tablename__ = "scan_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    uuid: Mapped[str] = mapped_column(
        String(36), unique=True, nullable=False, default=_generate_uuid
    )
    job_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("scan_jobs.id"), nullable=False
    )
    video_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    video_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)

    # ── Fingerprint Analysis ─────────────────────────────────────────
    similarity_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    matched_video_path: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)

    # ── Deepfake Analysis ────────────────────────────────────────────
    deepfake_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    deepfake_confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    deepfake_model_used: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # ── Watermark Analysis ───────────────────────────────────────────
    watermark_present_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    watermark_tampering_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    watermark_confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # ── Metadata Forensics ───────────────────────────────────────────
    metadata_anomaly_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    metadata_details: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # ── Audio Forensics ──────────────────────────────────────────────
    audio_anomaly_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    audio_details: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # ── OCR Results ──────────────────────────────────────────────────
    ocr_results: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # ── Logo Detection ───────────────────────────────────────────────
    logo_detections: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # ── Composite Risk ───────────────────────────────────────────────
    risk_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    risk_level: Mapped[Optional[RiskLevel]] = mapped_column(
        Enum(RiskLevel), nullable=True
    )
    risk_confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    risk_explanation: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    recommended_action: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # ── Evidence ─────────────────────────────────────────────────────
    evidence_screenshots: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    heatmap_path: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    frame_analysis_details: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # ── Timestamps ───────────────────────────────────────────────────
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, nullable=False
    )

    # Relationships
    job: Mapped["ScanJob"] = relationship(back_populates="results")

    __table_args__ = (
        Index("idx_scan_results_job_id", "job_id"),
        Index("idx_scan_results_risk_level", "risk_level"),
        Index("idx_scan_results_created_at", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<ScanResult {self.video_path} risk={self.risk_level}>"


class Report(Base):
    """Generated forensic reports."""

    __tablename__ = "reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    uuid: Mapped[str] = mapped_column(
        String(36), unique=True, nullable=False, default=_generate_uuid, index=True
    )
    job_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("scan_jobs.id"), nullable=True
    )
    report_type: Mapped[str] = mapped_column(
        String(20), nullable=False, default="pdf"
    )  # pdf, json, csv
    file_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    file_size_bytes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    generated_by: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, nullable=False
    )

    __table_args__ = (
        Index("idx_reports_job_id", "job_id"),
        Index("idx_reports_created_at", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<Report {self.uuid} ({self.report_type})>"


class AuditLog(Base):
    """Audit trail for security and compliance."""

    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    action: Mapped[AuditAction] = mapped_column(Enum(AuditAction), nullable=False)
    user_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=True
    )
    resource_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    resource_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    details: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, nullable=False
    )

    # Relationships
    user: Mapped[Optional["User"]] = relationship(back_populates="audit_logs")

    __table_args__ = (
        Index("idx_audit_logs_action", "action"),
        Index("idx_audit_logs_user_id", "user_id"),
        Index("idx_audit_logs_created_at", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<AuditLog {self.action.value} by user={self.user_id}>"
