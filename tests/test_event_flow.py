from unittest.mock import patch

from fastapi.testclient import TestClient

from src.main import app

client = TestClient(app)


@patch("src.clients.notifier_client.NotifierClient.send")
@patch("src.clients.orchestrator_client.OrchestratorClient.rollback")
def test_prod_rollback_creates_approval(mock_rollback, mock_send):
    mock_send.return_value = {"status": "sent"}
    payload = {
        "project_id": "payments-api",
        "environment_id": "prod",
        "severity": "high",
        "signal": "P99 latency spiked to 4s after the 14:30 deploy",
        "context": {"last_deploy": "v2.3.1"},
        "timestamp": "2024-04-03T14:45:00Z"
    }

    response = client.post("/webhooks/events", json=payload)
    assert response.status_code == 202
    body = response.json()
    assert body["status"] == "awaiting_approval"
    assert "approval_id" in body
    mock_rollback.assert_not_called()


@patch("src.clients.orchestrator_client.OrchestratorClient.restart")
def test_qa_restart_executes_automatically(mock_restart):
    mock_restart.return_value = {"status": "success", "action": "restart"}
    payload = {
        "project_id": "orders-api",
        "environment_id": "qa",
        "severity": "medium",
        "signal": "pod crash detected with OOM",
        "context": {},
        "timestamp": "2024-04-03T14:45:00Z"
    }

    response = client.post("/webhooks/events", json=payload)
    assert response.status_code == 202
    body = response.json()
    assert body["status"] == "executed"
    assert body["execution_result"]["status"] == "success"
    mock_restart.assert_called_once()
