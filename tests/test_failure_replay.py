from app.api.chat import detect_failure_reasons


def test_detect_failure_reasons_for_low_confidence_knowledge() -> None:
    reasons = detect_failure_reasons(
        intent="knowledge_qa",
        confidence=0.6,
        references=[],
        confidence_threshold=0.75,
    )
    assert "low_confidence" in reasons
    assert "no_references" in reasons


def test_detect_failure_reasons_for_handoff() -> None:
    reasons = detect_failure_reasons(
        intent="handoff_human",
        confidence=0.93,
        references=[],
        confidence_threshold=0.75,
    )
    assert "handoff_human" in reasons
