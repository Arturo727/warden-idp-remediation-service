from datetime import datetime, timezone
import json
import logging

from sqlalchemy.orm import Session

from src.models.approval import ApprovalModel
from src.models.event import EventModel
from src.models.execution import ExecutionModel
from src.services.action_service import ActionService

logger = logging.getLogger(__name__)


class ApprovalService:
    def __init__(self) -> None:
        self.action_service = ActionService()

    def _persist_execution(self, db: Session, event_id: int, action: str, executor_type: str, api_trace: dict) -> ExecutionModel:
        execution = ExecutionModel(
            event_id=event_id,
            action=action,
            executor_type=executor_type,
            status=api_trace.get("status", "success"),
            endpoint=api_trace.get("endpoint"),
            request_json=json.dumps(api_trace.get("request")) if api_trace.get("request") is not None else None,
            response_json=json.dumps(api_trace.get("response")) if api_trace.get("response") is not None else None,
            result_json=json.dumps(api_trace),
        )
        db.add(execution)
        db.commit()
        db.refresh(execution)
        return execution

    def approve(self, db: Session, approval_id: int, resolved_by: str, resolution_note: str) -> dict:
        approval = db.query(ApprovalModel).filter(ApprovalModel.id == approval_id).first()
        if not approval:
            raise ValueError("approval not found")
        if approval.status != "pending":
            raise ValueError("approval is not pending")

        event = db.query(EventModel).filter(EventModel.id == approval.event_id).first()
        if not event:
            raise ValueError("event not found")

        logger.info(
            "approval_execute_handler",
            extra={
                "approval_id": approval.id,
                "event_id": event.id,
                "action_approved": approval.action,
                "resolved_by": resolved_by,
            },
        )
        api_trace = self.action_service.execute(approval.action, event.project_id, event.environment_id)
        self._persist_execution(db, event.id, approval.action, "approval_execute_handler", api_trace)

        approval.status = "approved"
        approval.resolved_by = resolved_by
        approval.resolution_note = resolution_note
        approval.resolved_at = datetime.now(timezone.utc)

        event.status = "approved"
        db.commit()

        return {
            "approval_id": approval.id,
            "status": approval.status,
            "event_id": event.id,
            "action_approved": approval.action,
            "result": api_trace,
        }

    def reject(self, db: Session, approval_id: int, resolved_by: str, resolution_note: str) -> dict:
        approval = db.query(ApprovalModel).filter(ApprovalModel.id == approval_id).first()
        if not approval:
            raise ValueError("approval not found")
        if approval.status != "pending":
            raise ValueError("approval is not pending")

        event = db.query(EventModel).filter(EventModel.id == approval.event_id).first()
        if not event:
            raise ValueError("event not found")

        logger.info(
            "approval_reject_handler",
            extra={
                "approval_id": approval.id,
                "event_id": event.id,
                "action_rejected": approval.action,
                "resolved_by": resolved_by,
            },
        )

        approval.status = "rejected"
        approval.resolved_by = resolved_by
        approval.resolution_note = resolution_note
        approval.resolved_at = datetime.now(timezone.utc)

        event.status = "rejected"
        db.commit()

        return {
            "approval_id": approval.id,
            "status": approval.status,
            "event_id": event.id,
            "action_rejected": approval.action,
        }
