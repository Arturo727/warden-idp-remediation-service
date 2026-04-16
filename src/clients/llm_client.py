import logging
from typing import Any, Dict, List, Optional, Tuple

from src.clients.groq_llm_client import GroqLLMClient
from src.config import settings
from src.domain.enums import Action
from src.domain.schemas import DecisionOut, EventIn

logger = logging.getLogger(__name__)


class MockLLMClient:
    def build_prompt(self, event: EventIn, history: list[dict]) -> dict:
        return {
            "provider": "mock",
            "task": "Heuristic fallback reasoning for remediation",
            "event": event.model_dump(mode="json"),
            "history": history,
            "guardrails": [
                "If severity is critical, safe_to_auto must be false.",
                "If confidence is below 0.7, safe_to_auto must be false.",
                "If environment is production and action is rollback or scale_up, safe_to_auto must be false."
            ],
        }

    def decide(self, event: EventIn, history: List[dict], error: Optional[str] = None) -> Tuple[DecisionOut, Dict[str, Any], Dict[str, Any], str, Optional[str]]:
        signal = event.signal.lower()

        if "latency" in signal and "deploy" in signal:
            decision = DecisionOut(action=Action.rollback, confidence=0.88, reasoning="High latency spike detected after a recent deploy. Historical context was considered when available.", safe_to_auto=True)
        elif "crash" in signal or "oom" in signal:
            decision = DecisionOut(action=Action.restart, confidence=0.82, reasoning="Service instability suggests restart as first remediation.", safe_to_auto=True)
        elif "cpu" in signal or "saturation" in signal:
            decision = DecisionOut(action=Action.scale_up, confidence=0.76, reasoning="CPU saturation suggests scaling the workload.", safe_to_auto=True)
        else:
            decision = DecisionOut(action=Action.notify_human, confidence=0.55, reasoning="Insufficient certainty to automate remediation.", safe_to_auto=False)

        prompt = {
            "api_name": "mock-llm",
            "endpoint": "local://mock-llm",
            "request": self.build_prompt(event, history),
        }
        response = {
            "api_name": "mock-llm",
            "response": {
                "provider": "mock",
                "fallback_reason": error,
                "decision": decision.model_dump(mode="json"),
                "history_items_used": len(history),
            },
            "status": "fallback",
        }
        return decision, prompt, response, "mock", error


class LLMClient:
    def __init__(self) -> None:
        self.mock_client = MockLLMClient()
        self.groq_client = GroqLLMClient()

    def decide(self, event: EventIn, history: List[dict]) -> Tuple[DecisionOut, Optional[Dict[str, Any]], Optional[Dict[str, Any]], str, Optional[str]]:
        llm_mode = ""
        if isinstance(event.context, dict):
            llm_mode = str(event.context.get("llm_mode", "")).strip().lower()

        if llm_mode == "without_llm":
            logger.info("llm_mode_without_llm_forcing_mock")
            return self.mock_client.decide(event, history, error="forced_without_llm")

        if (llm_mode in {"with_llm", "with_llm_context"} or settings.llm_mode == "groq") and settings.groq_api_key:
            try:
                decision, prompt, response = self.groq_client.decide(event, history)
                return decision, prompt, response, "groq", None
            except Exception as exc:
                logger.exception("groq_decision_failed_falling_back_to_mock")
                return self.mock_client.decide(event, history, error=str(exc))

        return self.mock_client.decide(event, history, error="groq_not_configured")
