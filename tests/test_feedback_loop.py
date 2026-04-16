from fastapi.testclient import TestClient

from src.main import app

client = TestClient(app)


def test_approval_feedback_is_persisted_and_visible():
    payload = {
        "project_id": "payments-api",
        "environment_id": "prod",
        "severity": "high",
        "signal": "P99 latency spiked to 4s after the 14:30 deploy",
        "context": {
            "workload_id": "payments-api",
            "llm_mode": "with_llm_context",
            "simulated_context_count": 3
        },
        "timestamp": "2024-04-03T14:45:00Z"
    }
    created = client.post("/webhooks/events", json=payload)
    assert created.status_code == 202
    approval_id = created.json()["approval_id"]
    event_id = created.json()["event_id"]

    approved = client.post(f"/approvals/{approval_id}/approve", json={"resolved_by": "human-on-call", "resolution_note": "approved in test"})
    assert approved.status_code == 200

    detail = client.get(f"/events/{event_id}")
    assert detail.status_code == 200
    body = detail.json()
    assert body["approval"]["status"] == "approved"
    assert body["approval"]["resolved_by"] == "human-on-call"
