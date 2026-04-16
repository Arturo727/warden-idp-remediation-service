import logging

from src.clients.notifier_client import NotifierClient
from src.clients.orchestrator_client import OrchestratorClient

logger = logging.getLogger(__name__)


class ActionService:
    def __init__(self) -> None:
        self.orchestrator = OrchestratorClient()
        self.notifier = NotifierClient()

    def execute(self, action: str, project_id: str, environment_id: str) -> dict:
        logger.info(
            "action_execute_requested",
            extra={"action": action, "project_id": project_id, "environment_id": environment_id},
        )

        if action == "rollback":
            result = self.orchestrator.rollback(project_id, environment_id)
        elif action == "restart":
            result = self.orchestrator.restart(project_id, environment_id)
        elif action == "scale_up":
            result = self.orchestrator.scale_up(project_id, environment_id)
        elif action == "notify_human":
            result = self.notifier.send(
                {
                    "message": f"Manual intervention required for {project_id} in {environment_id}",
                    "project_id": project_id,
                    "environment_id": environment_id,
                }
            )
        elif action == "no_action":
            result = {
                "api_name": "no_action",
                "endpoint": None,
                "request": {"project_id": project_id, "environment_id": environment_id},
                "response": {"status": "skipped", "action": "no_action"},
                "status": "skipped",
            }
        else:
            raise ValueError(f"unsupported action '{action}'")

        logger.info(
            "action_execute_result",
            extra={"action": action, "project_id": project_id, "environment_id": environment_id, "result": result},
        )
        return result
