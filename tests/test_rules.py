from datetime import UTC, datetime

from src.domain.enums import Action
from src.domain.rules import apply_safety_rules
from src.domain.schemas import DecisionOut, EventIn


def build_event(severity: str = "high", environment_id: str = "qa") -> EventIn:
    return EventIn(
        project_id="payments-api",
        environment_id=environment_id,
        severity=severity,
        signal="latency spike after deploy",
        context={},
        timestamp=datetime.now(UTC),
    )


def test_critical_always_disables_auto():
    event = build_event(severity="critical")
    decision = DecisionOut(action=Action.restart, confidence=0.95, reasoning="x", safe_to_auto=True)
    final_safe, reasons = apply_safety_rules(event, decision, 0.7)

    assert final_safe is False
    assert any("severity=critical" in r for r in reasons)


def test_low_confidence_disables_auto():
    event = build_event()
    decision = DecisionOut(action=Action.restart, confidence=0.4, reasoning="x", safe_to_auto=True)
    final_safe, _ = apply_safety_rules(event, decision, 0.7)

    assert final_safe is False


def test_prod_rollback_disables_auto():
    event = build_event(environment_id="prod")
    decision = DecisionOut(action=Action.rollback, confidence=0.95, reasoning="x", safe_to_auto=True)
    final_safe, _ = apply_safety_rules(event, decision, 0.7)

    assert final_safe is False


def test_qa_restart_can_still_be_auto():
    event = build_event(environment_id="qa")
    decision = DecisionOut(action=Action.restart, confidence=0.95, reasoning="x", safe_to_auto=True)
    final_safe, _ = apply_safety_rules(event, decision, 0.7)

    assert final_safe is True
