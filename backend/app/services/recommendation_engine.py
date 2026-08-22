"""
Recycling recommendation engine.

Deliberately separate from the AI layer: the AI only says "what does
this look like", never "what should you do with it". This module
answers the second question, and only from configured/seeded data —
never invented on the fly, and never presented as authoritative
municipal rule.
"""
from sqlalchemy.orm import Session

from app.models.core import RecyclingGuidance

_FALLBACK_GUIDANCE = (
    "We don't yet have specific guidance configured for this category. "
    "As a general rule: rinse if practical, keep it separate from general "
    "waste, and check your local recycling facility's rules for this material."
)

_GENERIC_DISCLAIMER = " Local recycling acceptance varies — please verify with your local facility."


def get_recycling_guidance(db: Session, category_code: str, locale: str = "default") -> str:
    row = (
        db.query(RecyclingGuidance)
        .filter(
            RecyclingGuidance.category_code == category_code,
            RecyclingGuidance.locale == locale,
            RecyclingGuidance.active.is_(True),
        )
        .order_by(RecyclingGuidance.version.desc())
        .first()
    )
    if row is None:
        return _FALLBACK_GUIDANCE
    return row.guidance_text + _GENERIC_DISCLAIMER
