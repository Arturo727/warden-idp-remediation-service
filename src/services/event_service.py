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

    def process_event(self, db: Session, payload: EventIn) -> dict:
        llm_mode = str(payload.context.get("llm_mode", "")).strip().lower() if isinstance(payload.context, dict) else ""
        logger.info("event_received", extra={
            "project_id": payload.project_id,
            "environment_id": payload.environment_id,
            "severity": getattr(payload.severity, "value", payload.severity),
            "llm_mode": llm_mode,
        })

        event = EventModel(
            project_id=payload.project_id,
            environment_id=payload.environment_id,
            severity=getattr(payload.severity, "value", payload.severity),
            signal=payload.signal,
            context_json=json.dumps(payload.context),
            timestamp=payload.timestamp,
            status=EventStatus.received.value,
        )
        db.add(event)
        db.commit()
        db.refresh(event)

        workload_id = payload.context.get("workload_id") if isinstance(payload.context, dict) else None
        history = []
        limit_override = None

        if llm_mode in {"with_llm", "with_llm_context"}:
            if llm_mode == "with_llm_context":
                raw = payload.context.get("simulated_context_count")
                try:
                    limit_override = int(raw)
                except (TypeError, ValueError):
                    limit_override = None
                if limit_override == 0:
                    limit_override = 0

            if llm_mode == "with_llm":
                history = self.history_service.get_history(db, payload.project_id, payload.environment_id, workload_id, limit_override=None)
            elif llm_mode == "with_llm_context" and limit_override != 0:
                history = self.history_service.get_history(db, payload.project_id, payload.environment_id, workload_id, limit_override=limit_override)

            history = [h for h in history if h["event_id"] != event.id]

        logger.info("history_resolution", extra={
            "project_id": payload.project_id,
            "environment_id": payload.environment_id,
            "llm_mode": llm_mode,
            "workload_id": workload_id,
            "history_items_used": len(history),
        })

        decision, final_safe, restrictions, llm_prompt, llm_response, llm_provider, llm_error = self.reasoning_service.reason(payload, history)

        logger.info("restrictions_applied", extra={
            "project_id": payload.project_id,
            "environment_id": payload.environment_id,
            "action": decision.action.value,
            "llm_safe_to_auto": decision.safe_to_auto,
            "final_safe_to_auto": final_safe,
            "restrictions": restrictions,
        })

        decision_row = DecisionModel(
            event_id=event.id,
            action=decision.action.value,
            confidence=decision.confidence,
            reasoning=decision.reasoning,
            llm_safe_to_auto=decision.safe_to_auto,
            final_safe_to_auto=final_safe,
            restrictions_applied_json=json.dumps(restrictions),
            llm_prompt_json=json.dumps(llm_prompt) if llm_prompt is not None else None,
            llm_response_json=json.dumps(llm_response) if llm_response is not None else None,
            llm_provider=llm_provider,
            llm_error=llm_error,
        )
        db.add(decision_row)
        db.commit()
        db.refresh(decision_row)

        if final_safe is True:
            logger.info("auto_execute_handler", extra={
                "event_id": event.id,
                "action": decision.action.value,
                "project_id": payload.project_id,
                "environment_id": payload.environment_id,
            })
            api_trace = self.action_service.execute(decision.action.value, payload.project_id, payload.environment_id)
            self._persist_execution(db, event.id, decision.action.value, "auto_execute_handler", api_trace)
            event.status = EventStatus.executed.value
            db.commit()
            return {
                "event_id": event.id,
                "status": event.status,
                "decision": decision.model_dump(mode="json"),
                "restrictions": restrictions,
                "history_items_used": len(history),
                "llm_provider": llm_provider,
                "llm_error": llm_error,
                "execution_result": api_trace,
            }

        # Approval path is mandatory when final_safe is false
        logger.info("approval_request_handler", extra={
            "event_id": event.id,
            "action_pending_approval": decision.action.value,
            "project_id": payload.project_id,
            "environment_id": payload.environment_id,
        })
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

        logger.info("notify_human_handler", extra={
            "event_id": event.id,
            "approval_id": approval.id,
            "action_pending_approval": decision.action.value,
        })
        notify_trace = self.action_service.execute("notify_human", payload.project_id, payload.environment_id)
        self._persist_execution(db, event.id, "notify_human", "notify_human_handler", notify_trace)

        return {
            "event_id": event.id,
            "status": event.status,
            "decision": decision.model_dump(mode="json"),
            "restrictions": restrictions,
            "history_items_used": len(history),
            "llm_provider": llm_provider,
            "llm_error": llm_error,
            "approval_id": approval.id,
            "approval_action": decision.action.value,
            "notification_result": notify_trace,
        }
