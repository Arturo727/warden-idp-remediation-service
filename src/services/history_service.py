import json
from typing import Optional
from sqlalchemy import desc
from sqlalchemy.orm import Session

from src.config import settings
from src.models.approval import ApprovalModel
from src.models.decision import DecisionModel
from src.models.event import EventModel
from src.models.execution import ExecutionModel


class HistoryService:
    def get_history(
        self,
        db: Session,
        project_id: str,
        environment_id: str,
        workload_id: Optional[str] = None,
        limit_override: Optional[int] = None,
    ) -> list[dict]:
        effective_limit = limit_override if isinstance(limit_override, int) and limit_override > 0 else settings.history_limit

        candidates = (
            db.query(EventModel)
            .filter(
                EventModel.project_id == project_id,
                EventModel.environment_id == environment_id,
            )
            .order_by(desc(EventModel.id))
            .limit(max(effective_limit * 5, effective_limit))
            .all()
        )

        selected_events: list[EventModel] = []
        for event in candidates:
            try:
                context = json.loads(event.context_json) if event.context_json else {}
            except Exception:
                context = {}

            event_workload_id = context.get("workload_id")
            if workload_id:
                if event_workload_id == workload_id:
                    selected_events.append(event)
            else:
                selected_events.append(event)

            if len(selected_events) >= effective_limit:
                break

        history: list[dict] = []
        for event in selected_events:
            decision = db.query(DecisionModel).filter(DecisionModel.event_id == event.id).first()
            approval = db.query(ApprovalModel).filter(ApprovalModel.event_id == event.id).first()
            execution = (
                db.query(ExecutionModel)
                .filter(ExecutionModel.event_id == event.id)
                .order_by(desc(ExecutionModel.id))
                .first()
            )

            result = None
            if execution and execution.result_json:
                try:
                    result = json.loads(execution.result_json)
                except Exception:
                    result = execution.result_json

            history.append(
                {
                    "event_id": event.id,
                    "signal": event.signal,
                    "decision": decision.action if decision else None,
                    "confidence": decision.confidence if decision else None,
                    "auto_or_approval": (
                        "auto" if execution and execution.executor_type in {"auto", "auto_execute_handler"}
                        else "approval_required" if approval else None
                    ),
                    "approval_status": approval.status if approval else None,
                    "human_feedback": approval.status if approval and approval.status in {"approved", "rejected"} else None,
                    "resolved_by": approval.resolved_by if approval else None,
                    "resolution_note": approval.resolution_note if approval else None,
                    "result": result,
                }
            )
        return history
