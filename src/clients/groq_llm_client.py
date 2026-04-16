import json
from typing import Any

import httpx

from src.config import settings
from src.domain.enums import Action
from src.domain.schemas import DecisionOut, EventIn


class GroqLLMClient:
    def build_messages(self, event: EventIn, history: list[dict]) -> list[dict]:
        system_prompt = (
            "You are an SRE remediation assistant. "
            "Return ONLY one valid JSON object with exactly these keys: "
            "action, confidence, reasoning, safe_to_auto. "
            "Allowed action values: rollback, restart, scale_up, notify_human, no_action. "
            "confidence must be a number between 0 and 1. "
            "reasoning must be a short string. "
            "safe_to_auto must be a boolean. "
            "Do not echo the input. Do not include markdown. Do not include extra keys."
        )

        user_prompt = {
            "task": "Analyze the degradation event and produce a remediation decision.",
            "event": event.model_dump(mode="json"),
            "history": history,
            "guardrails": [
                "If severity is critical, safe_to_auto must be false.",
                "If confidence is below 0.7, safe_to_auto must be false.",
                "If environment is production and action is rollback or scale_up, safe_to_auto must be false."
            ],
            "output_contract": {
                "action": "rollback | restart | scale_up | notify_human | no_action",
                "confidence": 0.95,
                "reasoning": "short explanation",
                "safe_to_auto": True
            }
        }

        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": json.dumps(user_prompt)},
        ]

    def _extract_json_payload(self, content: str) -> dict[str, Any]:
        text = (content or "").strip()

        if text.startswith("```"):
            text = text.strip("`")
            if text.startswith("json"):
                text = text[4:].strip()

        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            start = text.find("{")
            end = text.rfind("}")
            if start == -1 or end == -1 or end <= start:
                raise ValueError(f"Groq returned non-JSON content: {content}")
            data = json.loads(text[start:end + 1])

        if not isinstance(data, dict):
            raise ValueError(f"Groq returned JSON that is not an object: {data}")

        if "decision" in data and isinstance(data["decision"], dict):
            data = data["decision"]
        elif "result" in data and isinstance(data["result"], dict):
            data = data["result"]
        elif "response" in data and isinstance(data["response"], dict):
            data = data["response"]

        return data

    def _normalize_decision(self, data: dict[str, Any]) -> DecisionOut:
        action = data.get("action")
        confidence = data.get("confidence")
        reasoning = data.get("reasoning")
        safe_to_auto = data.get("safe_to_auto")

        if isinstance(action, str):
            action = action.strip().lower()

        if action not in {a.value for a in Action}:
            raise ValueError(f"Invalid action returned by Groq: {action}")

        try:
            confidence = float(confidence)
        except (TypeError, ValueError):
            raise ValueError(f"Invalid confidence returned by Groq: {confidence}")

        if not isinstance(reasoning, str) or not reasoning.strip():
            raise ValueError(f"Invalid reasoning returned by Groq: {reasoning}")

        if isinstance(safe_to_auto, str):
            lowered = safe_to_auto.strip().lower()
            if lowered in {"true", "yes", "1"}:
                safe_to_auto = True
            elif lowered in {"false", "no", "0"}:
                safe_to_auto = False

        if not isinstance(safe_to_auto, bool):
            raise ValueError(f"Invalid safe_to_auto returned by Groq: {safe_to_auto}")

        return DecisionOut(
            action=Action(action),
            confidence=confidence,
            reasoning=reasoning.strip(),
            safe_to_auto=safe_to_auto,
        )

    def decide(self, event: EventIn, history: list[dict]) -> tuple[DecisionOut, dict, dict]:
        messages = self.build_messages(event, history)
        request_payload = {
            "model": settings.groq_model,
            "messages": messages,
            "temperature": 0.1,
            "response_format": {"type": "json_object"},
        }

        response = httpx.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {settings.groq_api_key}",
                "Content-Type": "application/json",
            },
            json=request_payload,
            timeout=20,
        )
        response.raise_for_status()
        raw_response = response.json()

        content = raw_response["choices"][0]["message"]["content"]
        extracted = self._extract_json_payload(content)
        decision = self._normalize_decision(extracted)

        return decision, {
            "api_name": "groq",
            "endpoint": "https://api.groq.com/openai/v1/chat/completions",
            "request": request_payload,
        }, {
            "api_name": "groq",
            "response": raw_response,
            "status": "success",
        }
