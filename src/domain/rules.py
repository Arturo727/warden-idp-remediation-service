from src.domain.schemas import DecisionOut, EventIn


def apply_safety_rules(event: EventIn, decision: DecisionOut, confidence_threshold: float) -> tuple[bool, list[str]]:
    restrictions: list[str] = []
    final_safe = bool(decision.safe_to_auto)

    severity = str(getattr(event.severity, "value", event.severity)).lower()
    environment = str(event.environment_id).lower()
    action = str(getattr(decision.action, "value", decision.action)).lower()
    confidence = float(decision.confidence)

    if severity == "critical":
        final_safe = False
        restrictions.append("severity=critical => safe_to_auto=false")

    if confidence < float(confidence_threshold):
        final_safe = False
        restrictions.append(f"confidence<{confidence_threshold} => safe_to_auto=false")

    if environment in {"prod", "production"} and action in {"rollback", "scale_up"}:
        final_safe = False
        restrictions.append("prod + rollback/scale_up => safe_to_auto=false")

    return final_safe, restrictions
