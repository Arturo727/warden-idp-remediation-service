import httpx

from src.config import settings
from src.domain.validators import validate_http_https_url


class NotifierClient:
    def send(self, payload: dict) -> dict:
        validate_http_https_url(settings.notifier_url, "NOTIFIER_URL")
        endpoint = f"{settings.notifier_url}/send"
        response = httpx.post(endpoint, json=payload, timeout=10)
        response.raise_for_status()
        body = response.json()
        return {
            "api_name": "mock-notifier",
            "endpoint": endpoint,
            "request": payload,
            "response": body,
            "status": "success",
        }
