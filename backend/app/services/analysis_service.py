"""
AnalysisService: orchestrates the full pipeline.

UPLOAD -> VALIDATE -> STRIP METADATA -> STORE -> AI ANALYZE
       -> VALIDATE AI OUTPUT -> APPLY CONFIDENCE THRESHOLDS
       -> RECOMMENDATION ENGINE -> PERSIST -> RETURN

Every stage has explicit failure handling; a failure never becomes a
silently-fabricated successful result.
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.ai.base import ConfidenceBand
from app.ai.factory import get_vision_provider
from app.core.config import get_settings
from app.models.core import ModelVersion, Scan, ScanObject, ScanStatus
from app.services.image_validation import ImageValidationError, strip_exif_and_reencode, validate_and_load_image
from app.storage.local_storage import get_object_storage


class AnalysisPipelineError(Exception):
    def __init__(self, code: str, message: str):
        self.code = code
        self.message = message
        super().__init__(message)


def _get_or_create_model_version(db: Session, provider_name: str, model_version: str, is_mock: bool) -> ModelVersion:
    existing = (
        db.query(ModelVersion)
        .filter(ModelVersion.provider == provider_name, ModelVersion.version == model_version)
        .first()
    )
    if existing:
        return existing
    mv = ModelVersion(provider=provider_name, name=provider_name, version=model_version, is_mock=is_mock)
    db.add(mv)
    db.flush()
    return mv


def run_analysis(db: Session, user_id: uuid.UUID, raw_image_bytes: bytes) -> Scan:
    settings = get_settings()

    # 1. Server-side validation (authoritative — never trusts the client).
    try:
        real_mime, _width, _height, image_hash = validate_and_load_image(raw_image_bytes)
    except ImageValidationError as exc:
        raise AnalysisPipelineError(exc.code, exc.message) from exc

    # 2. Privacy: strip EXIF/metadata before persisting.
    clean_bytes = strip_exif_and_reencode(raw_image_bytes, real_mime)

    # 3. Store under a random key — never the original filename.
    storage = get_object_storage()
    ext = {"image/jpeg": "jpg", "image/png": "png", "image/webp": "webp"}[real_mime]
    object_key = storage.put_object(clean_bytes, ext)

    scan = Scan(
        user_id=user_id,
        image_object_key=object_key,
        image_mime_type=real_mime,
        image_size_bytes=len(clean_bytes),
        image_hash=image_hash,
        status=ScanStatus.PROCESSING,
    )
    db.add(scan)
    db.flush()

    # 4. AI analysis. Any provider failure marks the scan FAILED — we
    # never fabricate a result when the provider is unavailable.
    try:
        provider = get_vision_provider()
        result = provider.analyze_image(clean_bytes, real_mime)
    except Exception as exc:
        scan.status = ScanStatus.FAILED
        scan.error_message = "AI analysis was unavailable. Please try again."
        db.flush()
        raise AnalysisPipelineError("AI_UNAVAILABLE", scan.error_message) from exc

    # 5. Validate/bound the AI output before trusting any of it.
    if not (0.0 <= result.overall_confidence <= 1.0):
        scan.status = ScanStatus.FAILED
        scan.error_message = "The analysis result was invalid and has been discarded."
        db.flush()
        raise AnalysisPipelineError("INVALID_AI_RESPONSE", scan.error_message)

    # 6. Apply the configured confidence thresholds — never overridden ad hoc.
    if result.overall_confidence >= settings.AI_CONFIDENCE_HIGH_THRESHOLD:
        band = ConfidenceBand.HIGH
    elif result.overall_confidence >= settings.AI_CONFIDENCE_LOW_THRESHOLD:
        band = ConfidenceBand.MEDIUM
    else:
        band = ConfidenceBand.LOW

    needs_review = result.needs_review or band == ConfidenceBand.LOW

    model_version = _get_or_create_model_version(db, result.provider_name, result.model_version, result.is_mock)

    scan.model_version_id = model_version.id
    scan.overall_confidence = result.overall_confidence
    scan.confidence_band = band.value
    scan.needs_review = needs_review
    scan.explanation = result.explanation
    scan.limitations_json = {"items": result.limitations}
    scan.status = ScanStatus.COMPLETED
    scan.completed_at = datetime.now(timezone.utc)

    for idx, candidate in enumerate(result.candidates):
        db.add(
            ScanObject(
                scan_id=scan.id,
                object_index=idx,
                category_code=candidate.category_code,
                confidence=candidate.confidence,
                evidence_json={"items": candidate.evidence},
            )
        )

    db.flush()
    return scan
