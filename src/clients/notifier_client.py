import httpx

from src.config import settings


class NotifierClient:
    def send(self, payload: dict) -> dict:
        response = httpx.post(f"{settings.notifier_url}/send", json=payload, timeout=10)
        response.raise_for_status()
        return response.json()
