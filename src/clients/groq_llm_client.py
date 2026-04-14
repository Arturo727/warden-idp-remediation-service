import json

import httpx

from src.config import settings
from src.domain.schemas import DecisionOut, EventIn


class GroqLLMClient:
    def decide(self, event: EventIn, history: list[dict]) -> DecisionOut:
        prompt = {
            "task": "You are an SRE remediation assistant. Analyze the event and return only valid JSON.",
            "event": event.model_dump(mode="json"),
            "history": history,
            "expected_schema": {
                "action": "rollback | restart | scale_up | notify_human | no_action",
                "confidence": "float between 0 and 1",
                "reasoning": "short explanation",
                "safe_to_auto": "boolean",
            },
        }

        response = httpx.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {settings.groq_api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": settings.groq_model,
                "messages": [
                    {
                        "role": "system",
                        "content": "Return only JSON. Do not wrap the output in markdown fences.",
                    },
                    {
                        "role": "user",
                        "content": json.dumps(prompt),
                    },
                ],
                "temperature": 0.1,
            },
            timeout=20,
        )
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"]
        data = json.loads(content)
        return DecisionOut(**data)
