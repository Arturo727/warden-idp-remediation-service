from fastapi.testclient import TestClient

from src.main import app

client = TestClient(app)


def test_with_llm_context_persists_prompt_and_response_from_mock():
    payload = {
        "project_id": "orders-api",
        "environment_id": "qa",
        "severity": "medium",
        "signal": "pod crash detected with OOM",
        "context": {
            "workload_id": "orders-api",
            "llm_mode": "with_llm_context",
            "simulated_context_count": 1
        },
        "timestamp": "2024-04-03T14:45:00Z"
    }
    created = client.post("/webhooks/events", json=payload)
    assert created.status_code == 202
    event_id = created.json()["event_id"]

    detail = client.get(f"/events/{event_id}")
    assert detail.status_code == 200
    assert detail.json()["decision"]["llm_prompt"] is not None
    assert detail.json()["decision"]["llm_response"] is not None
    assert detail.json()["decision"]["llm_provider"] == "mock"
