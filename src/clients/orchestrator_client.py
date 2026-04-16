import httpx

from src.config import settings
from src.domain.validators import validate_http_https_url


class OrchestratorClient:
    def rollback(self, project_id: str, environment_id: str) -> dict:
        return self._post("/rollback", project_id, environment_id)

    def restart(self, project_id: str, environment_id: str) -> dict:
        return self._post("/restart", project_id, environment_id)

    def scale_up(self, project_id: str, environment_id: str) -> dict:
        return self._post("/scale-up", project_id, environment_id)

    def _post(self, path: str, project_id: str, environment_id: str) -> dict:
        validate_http_https_url(settings.orchestrator_url, "ORCHESTRATOR_URL")
        payload = {"project_id": project_id, "environment_id": environment_id}
        endpoint = f"{settings.orchestrator_url}{path}"
        response = httpx.post(endpoint, json=payload, timeout=10)
        response.raise_for_status()
        body = response.json()
        return {
            "api_name": "mock-orchestrator",
            "endpoint": endpoint,
            "request": payload,
            "response": body,
            "status": "success",
        }
