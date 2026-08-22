"""
Vision provider abstraction.

The rest of the application depends only on this interface, never on a
specific AI vendor. This lets the real provider be swapped in later
(Phase 6) without touching any calling code.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum


class ConfidenceBand(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    UNKNOWN = "unknown"


@dataclass
class MaterialCandidate:
    category_code: str          # e.g. "PET", "HDPE", "UNKNOWN"
    confidence: float           # 0.0 - 1.0
    evidence: list[str] = field(default_factory=list)


@dataclass
class VisionAnalysisResult:
    """
    The ONLY shape the rest of the app is allowed to consume. Anything a
    provider returns must be normalized into this before it leaves app/ai/.
    """
    candidates: list[MaterialCandidate]
    overall_confidence: float
    confidence_band: ConfidenceBand
    needs_review: bool
    explanation: str
    limitations: list[str]
    provider_name: str
    model_version: str
    is_mock: bool


class VisionProvider(ABC):
    """Abstract interface every AI provider (mock or real) must implement."""

    @abstractmethod
    def analyze_image(self, image_bytes: bytes, content_type: str) -> VisionAnalysisResult:
        """Run analysis on raw, already-validated image bytes."""
        raise NotImplementedError

    @abstractmethod
    def health_check(self) -> bool:
        """Return True if the provider is reachable/configured correctly."""
        raise NotImplementedError
