from fastapi.testclient import TestClient

from src.main import app

client = TestClient(app)


def test_invalid_payload_missing_project_id():
    payload = {
        "environment_id": "prod",
        "severity": "high",
        "signal": "latency spike",
        "context": {},
        "timestamp": "2024-04-03T14:45:00Z"
    }
    response = client.post("/webhooks/events", json=payload)
    assert response.status_code == 422


def test_invalid_payload_severity():
    payload = {
        "project_id": "payments-api",
        "environment_id": "prod",
        "severity": "urgent",
        "signal": "latency spike",
        "context": {},
        "timestamp": "2024-04-03T14:45:00Z"
    }
    response = client.post("/webhooks/events", json=payload)
    assert response.status_code == 422


def test_invalid_context_type():
    payload = {
        "project_id": "orders-api",
        "environment_id": "qa",
        "severity": "medium",
        "signal": "pod crash detected with OOM",
        "context": [],
        "timestamp": "2024-04-03T14:45:00Z"
    }
    response = client.post("/webhooks/events", json=payload)
    assert response.status_code == 422


def test_invalid_context_url_scheme():
    payload = {
        "project_id": "orders-api",
        "environment_id": "qa",
        "severity": "medium",
        "signal": "pod crash detected with OOM",
        "context": {"trace_url": "ftp://bad.example.com/file"},
        "timestamp": "2024-04-03T14:45:00Z"
    }
    response = client.post("/webhooks/events", json=payload)
    assert response.status_code == 422
    assert "context_url_errors" in response.json()["detail"]
