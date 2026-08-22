"""
Audit logging. Append-only: no function here updates or deletes a
record, and no API route exposes update/delete for audit_events.
"""
import uuid

from sqlalchemy.orm import Session

from app.models.core import AuditEvent


def record_audit_event(
    db: Session,
    *,
    actor_user_id: uuid.UUID | None,
    action: str,
    target_type: str | None = None,
    target_id: str | None = None,
    metadata: dict | None = None,
) -> None:
    """
    Never pass passwords, tokens, API keys, or raw image bytes in `metadata`.
    """
    event = AuditEvent(
        actor_user_id=actor_user_id,
        action=action,
        target_type=target_type,
        target_id=target_id,
        metadata_json=metadata or {},
    )
    db.add(event)
    db.flush()
