import logging

from src.clients.groq_llm_client import GroqLLMClient
from src.config import settings
from src.domain.enums import Action
from src.domain.schemas import DecisionOut, EventIn

logger = logging.getLogger(__name__)


class MockLLMClient:
    def decide(self, event: EventIn, history: list[dict]) -> DecisionOut:
        signal = event.signal.lower()

        if "latency" in signal and "deploy" in signal:
            return DecisionOut(
                action=Action.rollback,
                confidence=0.88,
                reasoning="High latency spike detected after a recent deploy. Historical context was considered when available.",
                safe_to_auto=True,
            )

        if "crash" in signal or "oom" in signal:
            return DecisionOut(
                action=Action.restart,
                confidence=0.82,
                reasoning="Service instability suggests restart as first remediation.",
                safe_to_auto=True,
            )

        if "cpu" in signal:
            return DecisionOut(
                action=Action.scale_up,
                confidence=0.76,
                reasoning="CPU saturation suggests scaling the workload.",
                safe_to_auto=True,
            )

        return DecisionOut(
            action=Action.notify_human,
            confidence=0.55,
            reasoning="Insufficient certainty to automate remediation.",
            safe_to_auto=False,
        )


class LLMClient:
    def __init__(self) -> None:
        self.mock_client = MockLLMClient()
        self.groq_client = GroqLLMClient()

    def decide(self, event: EventIn, history: list[dict]) -> DecisionOut:
        if settings.llm_mode == "groq" and settings.groq_api_key:
            try:
                return self.groq_client.decide(event, history)
            except Exception:
                logger.exception("groq_decision_failed_falling_back_to_mock")
        return self.mock_client.decide(event, history)
