"""
MockVisionProvider — DEVELOPMENT / DEMO MODE ONLY.

This is NOT a trained model. It exists so the application can be built,
tested, and demoed end-to-end without requiring a paid external AI
provider or a not-yet-available trained classifier.

It must never be presented to an end user as a real prediction. The
caller (analysis service) is responsible for setting a UI-visible
"Demo AI analysis" label whenever `is_mock=True` is returned.

Behavior: deterministic per input (same image -> same result, useful for
tests) but varies across different images by hashing the image bytes,
so it is not the same hard-coded "PET 87%" answer every time. It also
deliberately produces the full range of outcomes (high confidence,
medium, low/uncertain, non-plastic, mixed) so the uncertainty path is
exercisable and demoable.
"""
import hashlib

from app.ai.base import ConfidenceBand, MaterialCandidate, VisionAnalysisResult, VisionProvider

_SCENARIOS: list[dict] = [
    {
        "candidates": [MaterialCandidate("PET", 0.91, ["transparent rigid container", "narrow neck shape"])],
        "overall_confidence": 0.91,
        "band": ConfidenceBand.HIGH,
        "needs_review": False,
        "explanation": "The object shows a transparent rigid body with a narrow neck, consistent with PET bottles.",
        "limitations": ["Estimated from visible shape/transparency only; no chemical verification performed."],
    },
    {
        "candidates": [MaterialCandidate("HDPE", 0.78, ["opaque rigid container", "thick wall texture"])],
        "overall_confidence": 0.78,
        "band": ConfidenceBand.HIGH,
        "needs_review": False,
        "explanation": "The object appears to be an opaque, thick-walled rigid container typical of HDPE.",
        "limitations": ["Visual estimate only; local recycling acceptance may vary."],
    },
    {
        "candidates": [
            MaterialCandidate("PP", 0.52, ["semi-rigid container", "possible lid"]),
            MaterialCandidate("PS", 0.31, ["semi-rigid container"]),
        ],
        "overall_confidence": 0.52,
        "band": ConfidenceBand.MEDIUM,
        "needs_review": True,
        "explanation": "Visible characteristics are consistent with more than one plastic type; evidence is not strong enough to choose one reliably.",
        "limitations": ["Ambiguous between PP and PS from this angle/lighting.", "A clearer, closer photo would improve confidence."],
    },
    {
        "candidates": [MaterialCandidate("UNKNOWN", 0.22, ["insufficient visual evidence"])],
        "overall_confidence": 0.22,
        "band": ConfidenceBand.LOW,
        "needs_review": True,
        "explanation": "We could not determine this material confidently from the photograph.",
        "limitations": ["Image may be too blurry, too dark, or the object too small/occluded.", "Please retake the photo with better lighting and the object fully in frame."],
    },
    {
        "candidates": [
            MaterialCandidate("LDPE", 0.61, ["flexible film material"]),
            MaterialCandidate("Multi-layer/Mixed", 0.35, ["overlapping wrapper layers"]),
        ],
        "overall_confidence": 0.55,
        "band": ConfidenceBand.MEDIUM,
        "needs_review": True,
        "explanation": "Multiple overlapping plastic items appear to be present in this photo.",
        "limitations": ["Mixed/overlapping objects reduce reliability of a single classification.", "Photographing one item at a time improves accuracy."],
    },
]


class MockVisionProvider(VisionProvider):
    provider_name = "mock"
    model_version = "mock-v0-demo"

    def analyze_image(self, image_bytes: bytes, content_type: str) -> VisionAnalysisResult:
        digest = hashlib.sha256(image_bytes).digest()
        scenario = _SCENARIOS[digest[0] % len(_SCENARIOS)]
        return VisionAnalysisResult(
            candidates=scenario["candidates"],
            overall_confidence=scenario["overall_confidence"],
            confidence_band=scenario["band"],
            needs_review=scenario["needs_review"],
            explanation=scenario["explanation"],
            limitations=scenario["limitations"],
            provider_name=self.provider_name,
            model_version=self.model_version,
            is_mock=True,
        )

    def health_check(self) -> bool:
        return True
