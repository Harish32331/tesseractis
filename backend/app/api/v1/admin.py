import uuid

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.audit.service import record_audit_event
from app.core.db import get_db
from app.core.errors import AppError
from app.models.core import AuditEvent, Feedback, Scan, ScanStatus, User, UserStatus
from app.security.deps import require_admin

router = APIRouter(prefix="/api/v1/admin", tags=["admin"])


@router.get("/analytics")
def analytics(admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    """
    All numbers below come from real database queries. If the tables are
    empty (no production usage yet), the counts will honestly be zero —
    never a fabricated placeholder statistic.
    """
    total_users = db.query(func.count(User.id)).scalar()
    total_scans = db.query(func.count(Scan.id)).scalar()
    completed = db.query(func.count(Scan.id)).filter(Scan.status == ScanStatus.COMPLETED).scalar()
    needs_review = db.query(func.count(Scan.id)).filter(Scan.needs_review.is_(True)).scalar()
    failed = db.query(func.count(Scan.id)).filter(Scan.status == ScanStatus.FAILED).scalar()

    return {
        "data_source": "live_database",
        "total_users": total_users,
        "total_scans": total_scans,
        "completed_scans": completed,
        "needs_review_scans": needs_review,
        "failed_scans": failed,
        "note": "Zero values reflect an environment with no production usage yet, not placeholder data.",
    }


@router.get("/scans/needs-review")
def scans_needing_review(admin: User = Depends(require_admin), db: Session = Depends(get_db), limit: int = 50):
    limit = max(1, min(limit, 200))
    scans = (
        db.query(Scan)
        .filter(Scan.needs_review.is_(True), Scan.deleted_at.is_(None))
        .order_by(Scan.created_at.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "id": str(s.id),
            "user_id": str(s.user_id),
            "confidence": s.overall_confidence,
            "confidence_band": s.confidence_band,
            "created_at": s.created_at.isoformat(),
        }
        for s in scans
    ]


@router.get("/feedback")
def all_feedback(admin: User = Depends(require_admin), db: Session = Depends(get_db), limit: int = 50):
    limit = max(1, min(limit, 200))
    rows = db.query(Feedback).order_by(Feedback.created_at.desc()).limit(limit).all()
    return [
        {
            "id": str(f.id),
            "scan_id": str(f.scan_id),
            "verdict": f.verdict.value,
            "corrected_category_code": f.corrected_category_code,
            "comment": f.comment,
            "created_at": f.created_at.isoformat(),
        }
        for f in rows
    ]


@router.get("/audit-events")
def audit_events(admin: User = Depends(require_admin), db: Session = Depends(get_db), limit: int = 100):
    limit = max(1, min(limit, 500))
    rows = db.query(AuditEvent).order_by(AuditEvent.created_at.desc()).limit(limit).all()
    return [
        {
            "id": str(e.id),
            "actor_user_id": str(e.actor_user_id) if e.actor_user_id else None,
            "action": e.action,
            "target_type": e.target_type,
            "target_id": e.target_id,
            "created_at": e.created_at.isoformat(),
        }
        for e in rows
    ]


@router.get("/users")
def list_users(admin: User = Depends(require_admin), db: Session = Depends(get_db), limit: int = 50):
    limit = max(1, min(limit, 200))
    users = db.query(User).order_by(User.created_at.desc()).limit(limit).all()
    return [
        {"id": str(u.id), "email": u.email, "role": u.role.value, "status": u.status.value, "created_at": u.created_at.isoformat()}
        for u in users
    ]


@router.patch("/users/{user_id}/disable")
def disable_user(user_id: uuid.UUID, admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    user = db.get(User, user_id)
    if user is None:
        raise AppError("NOT_FOUND", "User not found.", status_code=404)
    user.status = UserStatus.DISABLED
    record_audit_event(db, actor_user_id=admin.id, action="ADMIN_USER_DISABLED", target_type="user", target_id=str(user.id))
    db.commit()
    return {"status": "disabled"}
