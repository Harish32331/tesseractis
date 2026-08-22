"""
FastAPI dependencies for authentication and authorization.

The role check happens here, server-side, on every request to a
protected route. The frontend's route guards are UX only — this module
is the actual enforcement point, per the spec's non-negotiable rule
that authorization must never be trusted from the client.
"""
import uuid
from datetime import datetime, timezone

from fastapi import Depends, Request
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.db import get_db
from app.core.errors import AppError
from app.models.core import User, UserRole, UserSession, UserStatus
from app.security.passwords import hash_session_token

settings = get_settings()


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    token = request.cookies.get(settings.SESSION_COOKIE_NAME)
    if not token:
        raise AppError("NOT_AUTHENTICATED", "You must be logged in to do this.", status_code=401)

    token_hash = hash_session_token(token)
    session = (
        db.query(UserSession)
        .filter(UserSession.token_hash == token_hash)
        .first()
    )
    if session is None or session.revoked_at is not None:
        raise AppError("NOT_AUTHENTICATED", "Your session is invalid. Please log in again.", status_code=401)

    now = datetime.now(timezone.utc)
    if session.expires_at.replace(tzinfo=timezone.utc) < now:
        raise AppError("SESSION_EXPIRED", "Your session has expired. Please log in again.", status_code=401)

    user = db.get(User, session.user_id)
    if user is None or user.status != UserStatus.ACTIVE:
        raise AppError("NOT_AUTHENTICATED", "This account is not available.", status_code=401)

    return user


def require_admin(user: User = Depends(get_current_user)) -> User:
    if user.role != UserRole.ADMIN:
        raise AppError("FORBIDDEN", "You do not have permission to access this resource.", status_code=403)
    return user


def require_scan_owner_or_admin(scan_user_id: uuid.UUID, current_user: User) -> None:
    """Ownership check used by scan read/delete endpoints. Never rely on
    hiding a UI button — this is the actual enforcement."""
    if current_user.role == UserRole.ADMIN:
        return
    if scan_user_id != current_user.id:
        raise AppError("FORBIDDEN", "You do not have access to this resource.", status_code=403)
