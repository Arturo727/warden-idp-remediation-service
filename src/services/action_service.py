import logging

from src.clients.notifier_client import NotifierClient
from src.clients.orchestrator_client import OrchestratorClient
from src.domain.enums import Action

logger = logging.getLogger(__name__)


class ActionService:
    def __init__(self) -> None:
        self.orchestrator = OrchestratorClient()
        self.notifier = NotifierClient()

    def execute(self, action: str, project_id: str, environment_id: str) -> dict:
        logger.info(
            "executing_action",
            extra={"action": action, "project_id": project_id, "environment_id": environment_id},
        )

        if action == Action.rollback.value:
            return self.orchestrator.rollback(project_id, environment_id)
        if action == Action.restart.value:
            return self.orchestrator.restart(project_id, environment_id)
        if action == Action.scale_up.value:
            return self.orchestrator.scale_up(project_id, environment_id)
        if action == Action.notify_human.value:
            return self.notifier.send({"message": f"Manual intervention required for {project_id} in {environment_id}"})
        if action == Action.no_action.value:
            return {"status": "recorded", "message": "No action executed"}

        raise ValueError(f"unsupported action: {action}")
