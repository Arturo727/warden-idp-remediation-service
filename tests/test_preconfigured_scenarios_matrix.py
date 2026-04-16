from fastapi.testclient import TestClient

from src.main import app

client = TestClient(app)

SCENARIOS = [
    {
        "name": "restart_qa_auto",
        "payload": {
            "project_id": "orders-api",
            "environment_id": "qa",
            "severity": "medium",
            "signal": "pod crash detected with OOM",
            "context": {"workload_id": "orders-api-restart-qa", "llm_mode": "with_llm"},
            "timestamp": "2024-04-03T14:45:00Z"
        },
        "expected_status": "executed",
    },
    {
        "name": "rollback_prod_requires_approval",
        "payload": {
            "project_id": "payments-api",
            "environment_id": "prod",
            "severity": "high",
            "signal": "P99 latency spiked to 4s after the 14:30 deploy",
            "context": {"workload_id": "payments-api-rollback-prod", "llm_mode": "with_llm"},
            "timestamp": "2024-04-03T14:45:00Z"
        },
        "expected_status": "awaiting_approval",
        "expected_restriction_fragment": "prod + rollback/scale_up",
    },
    {
        "name": "scale_up_prod_requires_approval",
        "payload": {
            "project_id": "catalog-api",
            "environment_id": "prod",
            "severity": "high",
            "signal": "cpu saturation sustained above 90% for 10 minutes",
            "context": {"workload_id": "catalog-api-scale-prod", "llm_mode": "with_llm"},
            "timestamp": "2024-04-03T16:10:00Z"
        },
        "expected_status": "awaiting_approval",
        "expected_restriction_fragment": "prod + rollback/scale_up",
    },
    {
        "name": "notify_human_flow",
        "payload": {
            "project_id": "support-api",
            "environment_id": "stg",
            "severity": "medium",
            "signal": "multiple weak signals with inconclusive correlation",
            "context": {"workload_id": "support-api-notify-stg", "llm_mode": "with_llm"},
            "timestamp": "2024-04-03T17:00:00Z"
        },
        "expected_status": "awaiting_approval",
        "expected_restriction_fragment": "confidence<0.7",
    },
    {
        "name": "no_action_flow",
        "payload": {
            "project_id": "telemetry-api",
            "environment_id": "dev",
            "severity": "low",
            "signal": "temporary spike resolved before remediation",
            "context": {"workload_id": "telemetry-api-noaction-dev", "llm_mode": "with_llm"},
            "timestamp": "2024-04-03T18:00:00Z"
        },
        "expected_status": "executed",
    },
    {
        "name": "critical_always_requires_approval",
        "payload": {
            "project_id": "identity-api",
            "environment_id": "stg",
            "severity": "critical",
            "signal": "authentication failures spiked across all pods",
            "context": {"workload_id": "identity-api-critical-stg", "llm_mode": "with_llm"},
            "timestamp": "2024-04-03T15:00:00Z"
        },
        "expected_status": "awaiting_approval",
        "expected_restriction_fragment": "severity=critical",
    },
    {
        "name": "low_confidence_guardrail",
        "payload": {
            "project_id": "reports-api",
            "environment_id": "qa",
            "severity": "medium",
            "signal": "intermittent user complaints with no clear telemetry correlation",
            "context": {"workload_id": "reports-api-lowconfidence-qa", "llm_mode": "with_llm_context", "simulated_context_count": 0},
            "timestamp": "2024-04-03T19:00:00Z"
        },
        "expected_status": "awaiting_approval",
        "expected_restriction_fragment": "confidence<0.7",
    },
]


def test_preconfigured_scenarios_endpoint_returns_7_items():
    response = client.get("/preconfigured-scenarios")
    assert response.status_code == 200
    items = response.json()
    assert isinstance(items, list)
    assert len(items) >= 7
    ids = {item["id"] for item in items}
    expected = {
        "scenario-auto-restart-qa",
        "scenario-prod-rollback-approval",
        "scenario-cpu-scale-prod",
        "scenario-explicit-notify-human",
        "scenario-no-action-info",
        "scenario-critical-never-auto",
        "scenario-low-confidence",
    }
    assert expected.issubset(ids)


def test_preconfigured_scenarios_matrix_executes_core_flows():
    for scenario in SCENARIOS:
        response = client.post("/webhooks/events", json=scenario["payload"])
        assert response.status_code == 202, f"Scenario failed: {scenario['name']}, body={response.text}"
        body = response.json()
        assert body["status"] == scenario["expected_status"], f"Scenario failed: {scenario['name']}, body={body}"
        if scenario["expected_status"] == "awaiting_approval":
            assert "approval_id" in body
        if "expected_restriction_fragment" in scenario:
            joined = " | ".join(body.get("restrictions", []))
            assert scenario["expected_restriction_fragment"] in joined, f"Scenario failed: {scenario['name']}, restrictions={body.get('restrictions')}"
