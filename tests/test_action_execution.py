from fastapi.testclient import TestClient

from src.main import app

client = TestClient(app)


def test_restart_action_executes_when_safe():
    payload = {
        "project_id": "orders-api",
        "environment_id": "qa",
        "severity": "medium",
        "signal": "pod crash detected with OOM",
        "context": {
            "workload_id": "orders-api",
            "llm_mode": "with_llm"
        },
        "timestamp": "2024-04-03T14:45:00Z"
    }
    response = client.post("/webhooks/events", json=payload)
    assert response.status_code == 202
    body = response.json()
    assert body["status"] == "executed"
    assert "execution_result" in body
    assert body["execution_result"]["response"]["action"] == "restart"


def test_prod_rollback_creates_approval_and_notifies():
    payload = {
        "project_id": "payments-api",
        "environment_id": "prod",
        "severity": "high",
        "signal": "P99 latency spiked to 4s after the 14:30 deploy",
        "context": {
            "workload_id": "payments-api",
            "llm_mode": "with_llm"
        },
        "timestamp": "2024-04-03T14:45:00Z"
    }
    response = client.post("/webhooks/events", json=payload)
    assert response.status_code == 202
    body = response.json()
    assert body["status"] == "awaiting_approval"
    assert "approval_id" in body
    assert "notification_result" in body
    assert any("prod + rollback/scale_up" in r for r in body["restrictions"])
