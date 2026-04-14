import json
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from src.domain.enums import ApprovalStatus, EventStatus
from src.models.approval import ApprovalModel
from src.models.event import EventModel
from src.models.execution import ExecutionModel
from src.services.action_service import ActionService


class ApprovalService:
    def __init__(self) -> None:
        self.action_service = ActionService()

    def approve(self, db: Session, approval_id: int, resolved_by: str, resolution_note: str | None = None) -> dict:
        approval = db.query(ApprovalModel).filter(ApprovalModel.id == approval_id).first()
        if not approval:
            raise ValueError("approval not found")
        if approval.status != ApprovalStatus.pending.value:
            raise ValueError("approval is not pending")

        event = db.query(EventModel).filter(EventModel.id == approval.event_id).first()
        if not event:
            raise ValueError("event not found")

        result = self.action_service.execute(approval.action, event.project_id, event.environment_id)

        approval.status = ApprovalStatus.approved.value
        approval.resolved_by = resolved_by
        approval.resolution_note = resolution_note
        approval.resolved_at = datetime.now(UTC)

        execution = ExecutionModel(
            event_id=event.id,
            action=approval.action,
            executor_type="approved_human",
            status="success",
            result_json=json.dumps(result),
        )
        db.add(execution)
        event.status = EventStatus.executed.value
        db.commit()

        return {"approval_id": approval.id, "status": approval.status, "execution_result": result}

    def reject(self, db: Session, approval_id: int, resolved_by: str, resolution_note: str | None = None) -> dict:
        approval = db.query(ApprovalModel).filter(ApprovalModel.id == approval_id).first()
        if not approval:
            raise ValueError("approval not found")
        if approval.status != ApprovalStatus.pending.value:
            raise ValueError("approval is not pending")

        event = db.query(EventModel).filter(EventModel.id == approval.event_id).first()
        if not event:
            raise ValueError("event not found")

        approval.status = ApprovalStatus.rejected.value
        approval.resolved_by = resolved_by
        approval.resolution_note = resolution_note
        approval.resolved_at = datetime.now(UTC)
        event.status = EventStatus.rejected.value
        db.commit()

        return {"approval_id": approval.id, "status": approval.status}
