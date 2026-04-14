import httpx

from src.config import settings


class OrchestratorClient:
    def rollback(self, project_id: str, environment_id: str) -> dict:
        return self._post("/rollback", project_id, environment_id)

    def restart(self, project_id: str, environment_id: str) -> dict:
        return self._post("/restart", project_id, environment_id)

    def scale_up(self, project_id: str, environment_id: str) -> dict:
        return self._post("/scale-up", project_id, environment_id)

    def _post(self, path: str, project_id: str, environment_id: str) -> dict:
        payload = {"project_id": project_id, "environment_id": environment_id}
        response = httpx.post(f"{settings.orchestrator_url}{path}", json=payload, timeout=10)
        response.raise_for_status()
        return response.json()
