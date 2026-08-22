import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, File, Request, UploadFile
from sqlalchemy.orm import Session, selectinload

from app.audit.service import record_audit_event
from app.core.config import get_settings
from app.core.db import get_db
from app.core.errors import AppError
from app.models.core import Feedback, FeedbackVerdict, ModelVersion, Scan, User
from app.schemas.scan import FeedbackRequest, ScanObjectPublic, ScanPublic, ScanSummary
from app.security.deps import get_current_user, require_scan_owner_or_admin
from app.security.rate_limit import check_rate_limit
from app.services.analysis_service import AnalysisPipelineError, run_analysis
from app.services.recommendation_engine import get_recycling_guidance

router = APIRouter(prefix="/api/v1/scans", tags=["scans"])
settings = get_settings()


def _to_public(scan: Scan, model_version: ModelVersion | None) -> ScanPublic:
    return ScanPublic(
        id=scan.id,
        status=scan.status.value if hasattr(scan.status, "value") else scan.status,
        overall_confidence=scan.overall_confidence,
        confidence_band=scan.confidence_band,
        needs_review=scan.needs_review,
        explanation=scan.explanation,
        limitations=(scan.limitations_json or {}).get("items", []),
        is_mock_result=bool(model_version.is_mock) if model_version else False,
        model_provider=model_version.provider if model_version else None,
        model_version=model_version.version if model_version else None,
        objects=[
            ScanObjectPublic(
                category_code=o.category_code,
                confidence=o.confidence,
                evidence=(o.evidence_json or {}).get("items", []),
            )
            for o in scan.objects
        ],
        error_message=scan.error_message,
        created_at=scan.created_at,
        completed_at=scan.completed_at,
    )


@router.post("", response_model=ScanPublic, status_code=201)
async def create_and_run_scan(
    request: Request,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not check_rate_limit(
        f"ratelimit:upload:{current_user.id}",
        max_requests=settings.RATE_LIMIT_UPLOAD_PER_MINUTE,
        window_seconds=60,
    ):
        raise AppError("RATE_LIMITED", "Too many analysis requests. Please wait a moment and try again.", status_code=429)

    raw_bytes = await file.read()
    if len(raw_bytes) > settings.MAX_UPLOAD_BYTES:
        raise AppError(
            "IMAGE_TOO_LARGE",
            f"The uploaded image exceeds the {settings.MAX_UPLOAD_BYTES // (1024*1024)}MB limit.",
            status_code=413,
        )

    try:
        scan = run_analysis(db, current_user.id, raw_bytes)
    except AnalysisPipelineError as exc:
        db.commit()
        record_audit_event(db, actor_user_id=current_user.id, action="ANALYSIS_FAILED", metadata={"code": exc.code})
        db.commit()
        raise AppError(exc.code, exc.message, status_code=422) from exc

    record_audit_event(db, actor_user_id=current_user.id, action="ANALYSIS_CREATED", target_type="scan", target_id=str(scan.id))
    db.commit()
    db.refresh(scan)

    model_version = db.get(ModelVersion, scan.model_version_id) if scan.model_version_id else None
    return _to_public(scan, model_version)


@router.get("", response_model=list[ScanSummary])
def list_scans(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    limit: int = 20,
    offset: int = 0,
):
    limit = max(1, min(limit, 100))
    scans = (
        db.query(Scan)
        .filter(Scan.user_id == current_user.id, Scan.deleted_at.is_(None))
        .order_by(Scan.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    return scans


@router.get("/{scan_id}", response_model=ScanPublic)
def get_scan(scan_id: uuid.UUID, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    scan = (
        db.query(Scan)
        .options(selectinload(Scan.objects))
        .filter(Scan.id == scan_id, Scan.deleted_at.is_(None))
        .first()
    )
    if scan is None:
        raise AppError("NOT_FOUND", "Analysis not found.", status_code=404)

    require_scan_owner_or_admin(scan.user_id, current_user)

    record_audit_event(db, actor_user_id=current_user.id, action="ANALYSIS_VIEWED", target_type="scan", target_id=str(scan.id))
    db.commit()

    model_version = db.get(ModelVersion, scan.model_version_id) if scan.model_version_id else None
    return _to_public(scan, model_version)


@router.delete("/{scan_id}", status_code=204)
def delete_scan(scan_id: uuid.UUID, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    scan = db.query(Scan).filter(Scan.id == scan_id, Scan.deleted_at.is_(None)).first()
    if scan is None:
        raise AppError("NOT_FOUND", "Analysis not found.", status_code=404)

    require_scan_owner_or_admin(scan.user_id, current_user)

    scan.deleted_at = datetime.now(timezone.utc)
    record_audit_event(db, actor_user_id=current_user.id, action="ANALYSIS_DELETED", target_type="scan", target_id=str(scan.id))
    db.commit()
    return None


@router.post("/{scan_id}/feedback", status_code=201)
def submit_feedback(
    scan_id: uuid.UUID,
    payload: FeedbackRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    scan = db.query(Scan).filter(Scan.id == scan_id, Scan.deleted_at.is_(None)).first()
    if scan is None:
        raise AppError("NOT_FOUND", "Analysis not found.", status_code=404)

    require_scan_owner_or_admin(scan.user_id, current_user)

    if payload.verdict not in (v.value for v in FeedbackVerdict):
        raise AppError("VALIDATION_ERROR", "Invalid feedback verdict.", status_code=400)

    feedback = Feedback(
        scan_id=scan.id,
        user_id=current_user.id,
        verdict=FeedbackVerdict(payload.verdict),
        corrected_category_code=payload.corrected_category_code,
        comment=(payload.comment or "")[:2000] or None,
    )
    db.add(feedback)
    record_audit_event(db, actor_user_id=current_user.id, action="FEEDBACK_SUBMITTED", target_type="scan", target_id=str(scan.id))
    db.commit()
    return {"status": "recorded"}


@router.get("/{scan_id}/guidance")
def get_guidance(scan_id: uuid.UUID, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    scan = db.query(Scan).options(selectinload(Scan.objects)).filter(Scan.id == scan_id, Scan.deleted_at.is_(None)).first()
    if scan is None:
        raise AppError("NOT_FOUND", "Analysis not found.", status_code=404)
    require_scan_owner_or_admin(scan.user_id, current_user)

    guidance = {obj.category_code: get_recycling_guidance(db, obj.category_code) for obj in scan.objects}
    return {"guidance": guidance}
