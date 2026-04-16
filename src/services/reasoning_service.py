import logging
from typing import Any, Dict, List, Optional, Tuple

from src.clients.llm_client import LLMClient
from src.config import settings
from src.domain.rules import apply_safety_rules
from src.domain.scenario_registry import find_matching_scenario, scenario_forced_decision
from src.domain.schemas import DecisionOut, EventIn

logger = logging.getLogger(__name__)


class ReasoningService:
    def __init__(self) -> None:
        self.llm = LLMClient()

    def reason(
        self, event: EventIn, history: list[dict]
    ) -> Tuple[DecisionOut, bool, List[str], Optional[Dict[str, Any]], Optional[Dict[str, Any]], str, Optional[str]]:
        decision, llm_prompt, llm_response, llm_provider, llm_error = self.llm.decide(event, history)

        scenario = find_matching_scenario(event)
        scenario_restrictions: List[str] = []
        if scenario is not None:
            decision, override_label = scenario_forced_decision(scenario)
            scenario_restrictions.append(
                f"scenario_match={scenario.get('id')} => forced_action={decision.action.value}; source={override_label}"
            )

        final_safe, restrictions = apply_safety_rules(event, decision, settings.confidence_threshold)
        restrictions = scenario_restrictions + restrictions

        logger.info(
            "llm_decision",
            extra={
                "project_id": event.project_id,
                "environment_id": event.environment_id,
                "action": decision.action.value,
                "confidence": decision.confidence,
                "llm_safe_to_auto": decision.safe_to_auto,
                "final_safe_to_auto": final_safe,
                "history_size": len(history),
                "restrictions": restrictions,
                "llm_provider": llm_provider,
                "llm_error": llm_error,
            },
        )
        return decision, final_safe, restrictions, llm_prompt, llm_response, llm_provider, llm_error
