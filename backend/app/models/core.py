"""
Core ORM models.

Design notes:
- UUID primary keys throughout.
- Soft-delete (deleted_at) on user-owned, user-deletable data (scans).
- Audit events are append-only: no update/delete path is ever exposed.
"""
import uuid
from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base


class UserRole(str, PyEnum):
    USER = "user"
    ADMIN = "admin"


class UserStatus(str, PyEnum):
    ACTIVE = "active"
    DISABLED = "disabled"


class ScanStatus(str, PyEnum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class FeedbackVerdict(str, PyEnum):
    CORRECT = "correct"
    INCORRECT = "incorrect"
    UNSURE = "unsure"


def _uuid_col():
    return mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = _uuid_col()
    email: Mapped[str] = mapped_column(String(320), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole, name="user_role"), default=UserRole.USER, nullable=False)
    status: Mapped[UserStatus] = mapped_column(Enum(UserStatus, name="user_status"), default=UserStatus.ACTIVE, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    scans: Mapped[list["Scan"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    sessions: Mapped[list["UserSession"]] = relationship(back_populates="user", cascade="all, delete-orphan")


class UserSession(Base):
    """Opaque server-side sessions. The cookie holds a random token; only
    its hash is stored, so a DB leak does not directly yield valid sessions."""

    __tablename__ = "sessions"

    id: Mapped[uuid.UUID] = _uuid_col()
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    token_hash: Mapped[str] = mapped_column(String(128), unique=True, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    user: Mapped["User"] = relationship(back_populates="sessions")


class MaterialCategory(Base):
    __tablename__ = "material_categories"

    id: Mapped[uuid.UUID] = _uuid_col()
    code: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)  # e.g. "PET"
    label: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class RecyclingGuidance(Base):
    __tablename__ = "recycling_guidance"

    id: Mapped[uuid.UUID] = _uuid_col()
    category_code: Mapped[str] = mapped_column(String(64), ForeignKey("material_categories.code"), nullable=False, index=True)
    locale: Mapped[str] = mapped_column(String(16), default="default", nullable=False)
    guidance_text: Mapped[str] = mapped_column(Text, nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ModelVersion(Base):
    __tablename__ = "model_versions"

    id: Mapped[uuid.UUID] = _uuid_col()
    provider: Mapped[str] = mapped_column(String(64), nullable=False)   # "mock" | "real-provider-name"
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    version: Mapped[str] = mapped_column(String(64), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_mock: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Scan(Base):
    """A single analysis of one uploaded photograph."""

    __tablename__ = "scans"

    id: Mapped[uuid.UUID] = _uuid_col()
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    image_object_key: Mapped[str] = mapped_column(String(512), nullable=False)  # random key, never original filename
    image_mime_type: Mapped[str] = mapped_column(String(64), nullable=False)
    image_size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    image_hash: Mapped[str] = mapped_column(String(128), nullable=False)  # sha256 for dedupe / integrity
    status: Mapped[ScanStatus] = mapped_column(Enum(ScanStatus, name="scan_status"), default=ScanStatus.PENDING, nullable=False, index=True)
    model_version_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("model_versions.id"), nullable=True)
    overall_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    confidence_band: Mapped[str | None] = mapped_column(String(16), nullable=True)  # high|medium|low|unknown
    needs_review: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    explanation: Mapped[str | None] = mapped_column(Text, nullable=True)
    limitations_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)

    __table_args__ = (
        CheckConstraint(
            "overall_confidence IS NULL OR (overall_confidence >= 0 AND overall_confidence <= 1)",
            name="ck_scan_confidence_bounds",
        ),
    )

    user: Mapped["User"] = relationship(back_populates="scans")
    objects: Mapped[list["ScanObject"]] = relationship(back_populates="scan", cascade="all, delete-orphan")
    feedback: Mapped[list["Feedback"]] = relationship(back_populates="scan", cascade="all, delete-orphan")


class ScanObject(Base):
    """One detected material candidate within a scan (a scan may have several)."""

    __tablename__ = "scan_objects"

    id: Mapped[uuid.UUID] = _uuid_col()
    scan_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("scans.id", ondelete="CASCADE"), nullable=False, index=True)
    object_index: Mapped[int] = mapped_column(Integer, nullable=False)
    category_code: Mapped[str] = mapped_column(String(64), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    evidence_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    __table_args__ = (
        CheckConstraint("confidence >= 0 AND confidence <= 1", name="ck_scan_object_confidence_bounds"),
    )

    scan: Mapped["Scan"] = relationship(back_populates="objects")


class Feedback(Base):
    __tablename__ = "feedback"

    id: Mapped[uuid.UUID] = _uuid_col()
    scan_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("scans.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    verdict: Mapped[FeedbackVerdict] = mapped_column(Enum(FeedbackVerdict, name="feedback_verdict"), nullable=False)
    corrected_category_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    scan: Mapped["Scan"] = relationship(back_populates="feedback")


class AuditEvent(Base):
    """Append-only. No API ever exposes update or delete for this table."""

    __tablename__ = "audit_events"

    id: Mapped[uuid.UUID] = _uuid_col()
    actor_user_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    action: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    target_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    target_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    metadata_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)
