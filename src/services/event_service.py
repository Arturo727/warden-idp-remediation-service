import json
import logging

from sqlalchemy.orm import Session

from src.domain.enums import ApprovalStatus, EventStatus
from src.domain.schemas import EventIn
from src.models.approval import ApprovalModel
from src.models.decision import DecisionModel
from src.models.event import EventModel
from src.models.execution import ExecutionModel
from src.services.action_service import ActionService
from src.services.history_service import HistoryService
from src.services.reasoning_service import ReasoningService

logger = logging.getLogger(__name__)


class EventService:
    def __init__(self) -> None:
        self.history_service = HistoryService()
        self.reasoning_service = ReasoningService()
        self.action_service = ActionService()

    def process_event(self, db: Session, payload: EventIn) -> dict:
        logger.info(
            "event_received",
            extra={
                "project_id": payload.project_id,
                "environment_id": payload.environment_id,
                "severity": payload.severity.value,
            },
        )

        event = EventModel(
            project_id=payload.project_id,
            environment_id=payload.environment_id,
            severity=payload.severity.value,
            signal=payload.signal,
            context_json=json.dumps(payload.context),
            timestamp=payload.timestamp,
            status=EventStatus.received.value,
        )
        db.add(event)
        db.commit()
        db.refresh(event)

        workload_id = payload.context.get("workload_id") if isinstance(payload.context, dict) else None
        history = self.history_service.get_history(db, payload.project_id, payload.environment_id, workload_id)
        history = [h for h in history if h["event_id"] != event.id]

        decision, final_safe, restrictions = self.reasoning_service.reason(payload, history)

        decision_row = DecisionModel(
            event_id=event.id,
            action=decision.action.value,
            confidence=decision.confidence,
            reasoning=decision.reasoning,
            llm_safe_to_auto=decision.safe_to_auto,
            final_safe_to_auto=final_safe,
            restrictions_applied_json=json.dumps(restrictions),
        )
        db.add(decision_row)
        db.commit()
        db.refresh(decision_row)

        if final_safe:
            result = self.action_service.execute(decision.action.value, payload.project_id, payload.environment_id)
            execution = ExecutionModel(
                event_id=event.id,
                action=decision.action.value,
                executor_type="auto",
                status="success",
                result_json=json.dumps(result),
            )
            db.add(execution)
            event.status = EventStatus.executed.value
            db.commit()

            return {
                "event_id": event.id,
                "status": event.status,
                "decision": decision.model_dump(mode="json"),
                "restrictions": restrictions,
                "execution_result": result,
            }

        approval = ApprovalModel(
            event_id=event.id,
            decision_id=decision_row.id,
            action=decision.action.value,
            status=ApprovalStatus.pending.value,
        )
        db.add(approval)
        event.status = EventStatus.awaiting_approval.value
        db.commit()
        db.refresh(approval)

        self.action_service.execute("notify_human", payload.project_id, payload.environment_id)

        return {
            "event_id": event.id,
            "status": event.status,
            "decision": decision.model_dump(mode="json"),
            "restrictions": restrictions,
            "approval_id": approval.id,
        }
