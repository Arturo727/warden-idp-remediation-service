from fastapi.testclient import TestClient

from src.main import app

client = TestClient(app)


def test_no_history_behaves_as_before():
    payload = {
        "project_id": "orders-api",
        "environment_id": "qa",
        "severity": "medium",
        "signal": "pod crash detected with OOM",
        "context": {
            "workload_id": "new-api",
            "llm_mode": "with_llm"
        },
        "timestamp": "2024-04-03T15:00:00Z"
    }
    response = client.post("/webhooks/events", json=payload)
    assert response.status_code == 202
    assert response.json()["history_items_used"] == 0


def test_with_llm_context_uses_workload_history():
    payload1 = {
        "project_id": "payments-api",
        "environment_id": "prod",
        "severity": "high",
        "signal": "P99 latency spiked to 4s after the 14:30 deploy",
        "context": {
            "workload_id": "payments-api",
            "llm_mode": "without_llm"
        },
        "timestamp": "2024-04-03T14:45:00Z"
    }
    r1 = client.post("/webhooks/events", json=payload1)
    assert r1.status_code == 202

    payload2 = {
        "project_id": "payments-api",
        "environment_id": "prod",
        "severity": "high",
        "signal": "P99 latency spiked to 4s after the 14:30 deploy",
        "context": {
            "workload_id": "payments-api",
            "llm_mode": "with_llm_context",
            "simulated_context_count": 5
        },
        "timestamp": "2024-04-03T14:50:00Z"
    }
    r2 = client.post("/webhooks/events", json=payload2)
    assert r2.status_code == 202
    assert "history_items_used" in r2.json()
    assert r2.json()["history_items_used"] >= 1
