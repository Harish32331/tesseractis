"""
Selects the active VisionProvider based on configuration.

AI_PROVIDER=mock  -> MockVisionProvider (always available, no credentials needed)
AI_PROVIDER=real  -> RealVisionProvider (Phase 6 — not yet implemented; will
                     raise a clear, safe error rather than silently falling
                     back to mock, so misconfiguration is never disguised
                     as a real result).
"""
from app.ai.base import VisionProvider
from app.ai.mock_provider import MockVisionProvider
from app.core.config import get_settings


def get_vision_provider() -> VisionProvider:
    settings = get_settings()
    if settings.AI_PROVIDER == "mock":
        return MockVisionProvider()
    if settings.AI_PROVIDER == "real":
        # Phase 6 will implement RealVisionProvider against a chosen
        # vision-capable API once that decision is made. Until then we
        # fail loudly instead of silently serving mock results as real.
        raise NotImplementedError(
            "AI_PROVIDER=real is configured but RealVisionProvider is not "
            "implemented yet (scheduled for Phase 6). Set AI_PROVIDER=mock "
            "for development, or implement app/ai/real_provider.py."
        )
    raise ValueError(f"Unknown AI_PROVIDER setting: {settings.AI_PROVIDER!r}")
