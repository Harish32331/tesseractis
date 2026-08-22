import uuid
from datetime import datetime

from pydantic import BaseModel


class ScanObjectPublic(BaseModel):
    category_code: str
    confidence: float
    evidence: list[str] = []

    model_config = {"from_attributes": True}


class ScanPublic(BaseModel):
    id: uuid.UUID
    status: str
    overall_confidence: float | None
    confidence_band: str | None
    needs_review: bool
    explanation: str | None
    limitations: list[str] = []
    is_mock_result: bool
    model_provider: str | None
    model_version: str | None
    objects: list[ScanObjectPublic] = []
    error_message: str | None
    created_at: datetime
    completed_at: datetime | None

    model_config = {"from_attributes": True}


class ScanSummary(BaseModel):
    id: uuid.UUID
    status: str
    overall_confidence: float | None
    confidence_band: str | None
    needs_review: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class FeedbackRequest(BaseModel):
    verdict: str  # "correct" | "incorrect" | "unsure"
    corrected_category_code: str | None = None
    comment: str | None = None
