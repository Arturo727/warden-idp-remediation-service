import os
from pathlib import Path

import pytest

os.environ["DATABASE_URL"] = "sqlite:///./test_warden.db"
os.environ["LOG_DIR"] = "./logs_test"
os.environ["GROQ_API_KEY"] = ""
os.environ["ORCHESTRATOR_URL"] = "http://mock-orchestrator:8001"
os.environ["NOTIFIER_URL"] = "http://mock-notifier:8002"

test_db = Path("test_warden.db")
if test_db.exists():
    test_db.unlink()

from src.domain.enums import Action
from src.domain.schemas import DecisionOut


def _mock_decide(self, event, history):
    signal = event.signal.lower()

    if "latency" in signal and "deploy" in signal:
        decision = DecisionOut(action=Action.rollback, confidence=0.88, reasoning="Mocked rollback after deploy latency spike.", safe_to_auto=True)
    elif "crash" in signal or "oom" in signal:
        decision = DecisionOut(action=Action.restart, confidence=0.82, reasoning="Mocked restart for crash/OOM.", safe_to_auto=True)
    elif "cpu" in signal or "saturation" in signal:
        decision = DecisionOut(action=Action.scale_up, confidence=0.76, reasoning="Mocked scale up for sustained CPU saturation.", safe_to_auto=True)
    elif "temporary spike resolved" in signal:
        decision = DecisionOut(action=Action.no_action, confidence=0.93, reasoning="Mocked no_action because incident self-resolved.", safe_to_auto=True)
    elif "intermittent user complaints" in signal or "inconclusive correlation" in signal:
        decision = DecisionOut(action=Action.notify_human, confidence=0.55, reasoning="Mocked low-confidence notify_human.", safe_to_auto=False)
    elif "authentication failures" in signal:
        decision = DecisionOut(action=Action.restart, confidence=0.91, reasoning="Mocked restart for authentication disruption.", safe_to_auto=True)
    else:
        decision = DecisionOut(action=Action.notify_human, confidence=0.55, reasoning="Mocked fallback notify_human.", safe_to_auto=False)

    prompt = {
        "api_name": "mock-llm",
        "endpoint": "local://mock-llm",
        "request": {
            "event": event.model_dump(mode="json"),
            "history": history,
        },
    }
    response = {
        "api_name": "mock-llm",
        "response": {
            "decision": decision.model_dump(mode="json"),
            "history_items_used": len(history),
        },
        "status": "success",
    }
    return decision, prompt, response, "mock", None


def _mock_restart(self, project_id, environment_id):
    return {
        "api_name": "mock-orchestrator",
        "endpoint": "http://mock-orchestrator:8001/restart",
        "request": {"project_id": project_id, "environment_id": environment_id},
        "response": {"status": "success", "action": "restart", "payload": {"project_id": project_id, "environment_id": environment_id}},
        "status": "success",
    }


def _mock_rollback(self, project_id, environment_id):
    return {
        "api_name": "mock-orchestrator",
        "endpoint": "http://mock-orchestrator:8001/rollback",
        "request": {"project_id": project_id, "environment_id": environment_id},
        "response": {"status": "success", "action": "rollback", "payload": {"project_id": project_id, "environment_id": environment_id}},
        "status": "success",
    }


def _mock_scale_up(self, project_id, environment_id):
    return {
        "api_name": "mock-orchestrator",
        "endpoint": "http://mock-orchestrator:8001/scale-up",
        "request": {"project_id": project_id, "environment_id": environment_id},
        "response": {"status": "success", "action": "scale_up", "payload": {"project_id": project_id, "environment_id": environment_id}},
        "status": "success",
    }


def _mock_send(self, payload):
    return {
        "api_name": "mock-notifier",
        "endpoint": "http://mock-notifier:8002/send",
        "request": payload,
        "response": {"status": "sent"},
        "status": "success",
    }


@pytest.fixture(autouse=True)
def mock_external_dependencies(monkeypatch):
    monkeypatch.setattr("src.clients.llm_client.LLMClient.decide", _mock_decide)
    monkeypatch.setattr("src.clients.orchestrator_client.OrchestratorClient.restart", _mock_restart)
    monkeypatch.setattr("src.clients.orchestrator_client.OrchestratorClient.rollback", _mock_rollback)
    monkeypatch.setattr("src.clients.orchestrator_client.OrchestratorClient.scale_up", _mock_scale_up)
    monkeypatch.setattr("src.clients.notifier_client.NotifierClient.send", _mock_send)
