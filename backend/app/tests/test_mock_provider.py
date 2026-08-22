from app.ai.base import ConfidenceBand
from app.ai.mock_provider import MockVisionProvider


def test_mock_provider_is_labeled_as_mock():
    provider = MockVisionProvider()
    result = provider.analyze_image(b"fake-image-bytes-1", "image/jpeg")
    assert result.is_mock is True
    assert result.provider_name == "mock"


def test_mock_provider_deterministic_for_same_input():
    provider = MockVisionProvider()
    r1 = provider.analyze_image(b"same-bytes", "image/jpeg")
    r2 = provider.analyze_image(b"same-bytes", "image/jpeg")
    assert r1.overall_confidence == r2.overall_confidence
    assert r1.candidates[0].category_code == r2.candidates[0].category_code


def test_mock_provider_produces_varied_outcomes_not_hardcoded_single_answer():
    provider = MockVisionProvider()
    seen_bands = set()
    for i in range(20):
        result = provider.analyze_image(f"image-{i}".encode(), "image/jpeg")
        seen_bands.add(result.confidence_band)
    # Must exercise more than one confidence band across varied inputs —
    # a fake demo that always says "PET 87%" would fail this test.
    assert len(seen_bands) > 1


def test_mock_provider_confidence_is_bounded():
    provider = MockVisionProvider()
    for i in range(10):
        result = provider.analyze_image(f"img-{i}".encode(), "image/jpeg")
        assert 0.0 <= result.overall_confidence <= 1.0
        for c in result.candidates:
            assert 0.0 <= c.confidence <= 1.0


def test_low_confidence_never_silently_hidden():
    """
    Whenever confidence_band is LOW, needs_review must be True and
    limitations must be non-empty — the system must never present an
    uncertain result as if it were reliable.
    """
    provider = MockVisionProvider()
    found_low = False
    for i in range(20):
        result = provider.analyze_image(f"probe-{i}".encode(), "image/jpeg")
        if result.confidence_band == ConfidenceBand.LOW:
            found_low = True
            assert result.needs_review is True
            assert len(result.limitations) > 0
    assert found_low, "Test setup issue: no LOW-confidence scenario was hit in 20 tries."
