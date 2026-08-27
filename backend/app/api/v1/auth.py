from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy.orm import Session

from app.audit.service import record_audit_event
from app.core.config import get_settings
from app.core.db import get_db
from app.core.errors import AppError
from app.models.core import User, UserSession
from app.schemas.auth import LoginRequest, RegisterRequest, UserPublic
from app.security.deps import get_current_user
from app.security.passwords import (
    generate_session_token,
    hash_password,
    hash_session_token,
    verify_password,
)
from app.security.rate_limit import check_rate_limit

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])
settings = get_settings()


def _client_key(request: Request, prefix: str) -> str:
    # X-Forwarded-For would be used behind a real proxy; for local dev,
    # client.host is sufficient.
    ip = request.client.host if request.client else "unknown"
    return f"ratelimit:{prefix}:{ip}"


def _set_session_cookie(response: Response, token: str) -> None:
    # Cross-origin frontend (Vercel) + backend (Render) requires SameSite=None
    # so the cookie travels on cross-site fetch requests. SameSite=None is only
    # honored by browsers when Secure is also true (i.e. in production/HTTPS).
    samesite = "none" if settings.SESSION_COOKIE_SECURE else "lax"
    response.set_cookie(
        key=settings.SESSION_COOKIE_NAME,
        value=token,
        httponly=True,
        secure=settings.SESSION_COOKIE_SECURE,
        samesite=samesite,
        max_age=settings.SESSION_TTL_SECONDS,
        path="/",
    )


@router.post("/register", response_model=UserPublic, status_code=201)
def register(payload: RegisterRequest, request: Request, response: Response, db: Session = Depends(get_db)):
    if not check_rate_limit(_client_key(request, "register"), max_requests=5, window_seconds=60):
        raise AppError("RATE_LIMITED", "Too many attempts. Please try again shortly.", status_code=429)

    existing = db.query(User).filter(User.email == payload.email.lower()).first()
    if existing is not None:
        # Account-enumeration-resistant: same error whether the email
        # exists or the password is later found weak.
        raise AppError("REGISTRATION_FAILED", "Unable to register with the provided details.", status_code=400)

    user = User(email=payload.email.lower(), password_hash=hash_password(payload.password))
    db.add(user)
    db.flush()

    token = generate_session_token()
    session = UserSession(
        user_id=user.id,
        token_hash=hash_session_token(token),
        expires_at=datetime.now(timezone.utc) + timedelta(seconds=settings.SESSION_TTL_SECONDS),
    )
    db.add(session)

    record_audit_event(db, actor_user_id=user.id, action="REGISTER", target_type="user", target_id=str(user.id))
    db.commit()

    _set_session_cookie(response, token)
    return user


@router.post("/login", response_model=UserPublic)
def login(payload: LoginRequest, request: Request, response: Response, db: Session = Depends(get_db)):
    if not check_rate_limit(_client_key(request, "login"), max_requests=settings.RATE_LIMIT_LOGIN_PER_MINUTE, window_seconds=60):
        raise AppError("RATE_LIMITED", "Too many login attempts. Please try again shortly.", status_code=429)

    user = db.query(User).filter(User.email == payload.email.lower()).first()

    # Constant-shape failure path: run a hash check even when the user
    # doesn't exist, so response timing doesn't reveal account existence.
    dummy_hash = "$argon2id$v=19$m=65536,t=3,p=4$AAAAAAAAAAAAAAAAAAAAAA$AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
    password_ok = verify_password(payload.password, user.password_hash if user else dummy_hash)

    if user is None or not password_ok:
        record_audit_event(db, actor_user_id=(user.id if user else None), action="LOGIN_FAILURE")
        db.commit()
        raise AppError("INVALID_CREDENTIALS", "Invalid email or password.", status_code=401)

    if user.status != "active":
        raise AppError("ACCOUNT_DISABLED", "This account is disabled.", status_code=403)

    token = generate_session_token()
    session = UserSession(
        user_id=user.id,
        token_hash=hash_session_token(token),
        expires_at=datetime.now(timezone.utc) + timedelta(seconds=settings.SESSION_TTL_SECONDS),
    )
    db.add(session)
    user.last_login_at = datetime.now(timezone.utc)
    record_audit_event(db, actor_user_id=user.id, action="LOGIN_SUCCESS")
    db.commit()

    _set_session_cookie(response, token)
    return user


@router.post("/logout", status_code=204)
def logout(request: Request, response: Response, db: Session = Depends(get_db)):
    token = request.cookies.get(settings.SESSION_COOKIE_NAME)
    if token:
        token_hash = hash_session_token(token)
        session = db.query(UserSession).filter(UserSession.token_hash == token_hash).first()
        if session is not None:
            session.revoked_at = datetime.now(timezone.utc)
            record_audit_event(db, actor_user_id=session.user_id, action="LOGOUT")
            db.commit()
    response.delete_cookie(settings.SESSION_COOKIE_NAME, path="/")
    return None


@router.get("/me", response_model=UserPublic)
def me(current_user: User = Depends(get_current_user)):
    return current_user
