from src.domain.enums import Action, Severity
from src.domain.schemas import DecisionOut, EventIn


def apply_safety_rules(event: EventIn, decision: DecisionOut, threshold: float) -> tuple[bool, list[str]]:
    reasons: list[str] = []
    final_safe = decision.safe_to_auto

    if event.severity == Severity.critical:
        final_safe = False
        reasons.append("severity=critical => safe_to_auto=false")

    if decision.confidence < threshold:
        final_safe = False
        reasons.append(f"confidence<{threshold} => safe_to_auto=false")

    is_prod = event.environment_id.lower() in {"prod", "production"}
    if is_prod and decision.action in {Action.rollback, Action.scale_up}:
        final_safe = False
        reasons.append("prod + rollback/scale_up => safe_to_auto=false")

    return final_safe, reasons
