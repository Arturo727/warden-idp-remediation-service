from __future__ import annotations

from typing import Any, Optional

from src.domain.enums import Action
from src.domain.schemas import DecisionOut, EventIn

PREDEFINED_SCENARIOS = [
    {
        "id": "scenario-auto-restart-qa",
        "name": "QA · Restart automático por OOM",
        "category": "restart",
        "description": "Caída por OOM en QA.",
        "project_id": "orders-api",
        "environment_id": "qa",
        "severity": "medium",
        "signal": "pod crash detected with OOM",
        "expected": "restart automático",
        "context": {"workload_id": "orders-api-restart-qa", "last_deploy": "v1.8.2", "cpu_usage": "61%", "error_rate": "4%"},
        "timestamp": "2024-04-03T14:45:00Z",
    },
    {
        "id": "scenario-prod-rollback-approval",
        "name": "PROD · Rollback requiere aprobación",
        "category": "rollback",
        "description": "Spike de latencia después de deploy en prod.",
        "project_id": "payments-api",
        "environment_id": "prod",
        "severity": "high",
        "signal": "P99 latency spiked to 4s after the 14:30 deploy",
        "expected": "approval para rollback",
        "context": {"workload_id": "payments-api-rollback-prod", "last_deploy": "v2.3.1", "cpu_usage": "85%", "error_rate": "12%"},
        "timestamp": "2024-04-03T14:45:00Z",
    },
    {
        "id": "scenario-cpu-scale-prod",
        "name": "PROD · Scale up no autoejecutable",
        "category": "scale_up",
        "description": "CPU alta en producción. La recomendación esperada es scale_up pero requiere aprobación.",
        "project_id": "catalog-api",
        "environment_id": "prod",
        "severity": "high",
        "signal": "cpu saturation sustained above 90% for 10 minutes",
        "expected": "approval para scale_up",
        "context": {"workload_id": "catalog-api-scale-prod", "last_deploy": "v3.4.0", "cpu_usage": "93%", "error_rate": "7%"},
        "timestamp": "2024-04-03T16:10:00Z",
    },
    {
        "id": "scenario-explicit-notify-human",
        "name": "Notify Human · Incidente ambiguo",
        "category": "notify_human",
        "description": "Señales ambiguas que deben escalarse a intervención humana.",
        "project_id": "support-api",
        "environment_id": "stg",
        "severity": "medium",
        "signal": "multiple weak signals with inconclusive correlation",
        "expected": "notify_human",
        "context": {"workload_id": "support-api-notify-stg", "last_deploy": "v2.0.1", "cpu_usage": "48%", "error_rate": "3%"},
        "timestamp": "2024-04-03T17:00:00Z",
    },
    {
        "id": "scenario-no-action-info",
        "name": "No Action · Evento informativo",
        "category": "no_action",
        "description": "Evento que se recuperó solo y no requiere remediación activa.",
        "project_id": "telemetry-api",
        "environment_id": "dev",
        "severity": "low",
        "signal": "temporary spike resolved before remediation",
        "expected": "no_action",
        "context": {"workload_id": "telemetry-api-noaction-dev", "last_deploy": "v0.9.8", "cpu_usage": "18%", "error_rate": "0.2%"},
        "timestamp": "2024-04-03T18:00:00Z",
    },
    {
        "id": "scenario-critical-never-auto",
        "name": "Critical · Nunca autoejecutar",
        "category": "guardrail",
        "description": "Severidad critical. safe_to_auto debe ser false siempre.",
        "project_id": "identity-api",
        "environment_id": "stg",
        "severity": "critical",
        "signal": "authentication failures spiked across all pods",
        "expected": "approval / notify_human",
        "context": {"workload_id": "identity-api-critical-stg", "last_deploy": "v5.1.0", "cpu_usage": "72%", "error_rate": "38%"},
        "timestamp": "2024-04-03T15:00:00Z",
    },
    {
        "id": "scenario-low-confidence",
        "name": "Baja confianza · Escalar a humano",
        "category": "guardrail",
        "description": "La respuesta esperada es notify_human por baja confianza.",
        "project_id": "reports-api",
        "environment_id": "qa",
        "severity": "medium",
        "signal": "intermittent user complaints with no clear telemetry correlation",
        "expected": "notify_human por baja confianza",
        "context": {"workload_id": "reports-api-lowconfidence-qa", "last_deploy": "v1.0.3", "cpu_usage": "31%", "error_rate": "2%"},
        "timestamp": "2024-04-03T19:00:00Z",
    }
]

SCENARIO_CATALOG = {
    (s["project_id"], s["environment_id"], s["severity"], s["signal"]) for s in PREDEFINED_SCENARIOS
}


def find_matching_scenario(event: EventIn) -> Optional[dict[str, Any]]:
    """Best-effort deterministic match for preconfigured scenarios.

    Priority:
    1. ui_scenario exact name match coming from frontend
    2. exact payload identity (project/environment/severity/signal)
    3. workload_id match when the scenario context defines it
    """
    ctx = event.context if isinstance(event.context, dict) else {}
    ui_scenario = str(ctx.get("ui_scenario", "")).strip().lower()
    workload_id = str(ctx.get("workload_id", "")).strip().lower()
    severity = str(getattr(event.severity, "value", event.severity)).strip().lower()

    if ui_scenario:
        for scenario in PREDEFINED_SCENARIOS:
            if scenario["name"].strip().lower() == ui_scenario:
                return scenario

    for scenario in PREDEFINED_SCENARIOS:
        if (
            scenario["project_id"] == event.project_id
            and scenario["environment_id"] == event.environment_id
            and str(scenario["severity"]).lower() == severity
            and scenario["signal"] == event.signal
        ):
            return scenario

    if workload_id:
        for scenario in PREDEFINED_SCENARIOS:
            scenario_workload = str(scenario.get("context", {}).get("workload_id", "")).strip().lower()
            if scenario_workload and scenario_workload == workload_id:
                return scenario

    return None


def scenario_forced_decision(scenario: dict[str, Any]) -> tuple[DecisionOut, str]:
    sid = scenario.get("id")

    if sid == "scenario-auto-restart-qa":
        return (
            DecisionOut(
                action=Action.restart,
                confidence=0.95,
                reasoning="Escenario preconfigurado: reinicio automático por OOM en QA.",
                safe_to_auto=True,
            ),
            "scenario_preconfigured_override",
        )
    if sid == "scenario-prod-rollback-approval":
        return (
            DecisionOut(
                action=Action.rollback,
                confidence=0.95,
                reasoning="Escenario preconfigurado: rollback en producción requiere aprobación.",
                safe_to_auto=False,
            ),
            "scenario_preconfigured_override",
        )
    if sid == "scenario-cpu-scale-prod":
        return (
            DecisionOut(
                action=Action.scale_up,
                confidence=0.91,
                reasoning="Escenario preconfigurado: scale_up en producción requiere aprobación.",
                safe_to_auto=False,
            ),
            "scenario_preconfigured_override",
        )
    if sid == "scenario-explicit-notify-human":
        return (
            DecisionOut(
                action=Action.notify_human,
                confidence=0.72,
                reasoning="Escenario preconfigurado: incidente ambiguo debe escalarse a humano.",
                safe_to_auto=False,
            ),
            "scenario_preconfigured_override",
        )
    if sid == "scenario-no-action-info":
        return (
            DecisionOut(
                action=Action.no_action,
                confidence=0.97,
                reasoning="Escenario preconfigurado: evento informativo sin remediación activa.",
                safe_to_auto=True,
            ),
            "scenario_preconfigured_override",
        )
    if sid == "scenario-critical-never-auto":
        return (
            DecisionOut(
                action=Action.notify_human,
                confidence=0.89,
                reasoning="Escenario preconfigurado: severidad critical nunca debe autoejecutarse.",
                safe_to_auto=False,
            ),
            "scenario_preconfigured_override",
        )
    if sid == "scenario-low-confidence":
        return (
            DecisionOut(
                action=Action.notify_human,
                confidence=0.55,
                reasoning="Escenario preconfigurado: baja confianza obliga a escalar a humano.",
                safe_to_auto=False,
            ),
            "scenario_preconfigured_override",
        )

    # Fallback by category if a new scenario is later added
    category = str(scenario.get("category", "")).strip().lower()
    if category in {a.value for a in Action}:
        action = Action(category)
        safe = action not in {Action.rollback, Action.scale_up, Action.notify_human}
        return (
            DecisionOut(
                action=action,
                confidence=0.8,
                reasoning="Escenario preconfigurado aplicado por categoría.",
                safe_to_auto=safe,
            ),
            "scenario_category_override",
        )

    return (
        DecisionOut(
            action=Action.notify_human,
            confidence=0.55,
            reasoning="Escenario no reconocido; se escala a humano por seguridad.",
            safe_to_auto=False,
        ),
        "scenario_fallback_override",
    )
