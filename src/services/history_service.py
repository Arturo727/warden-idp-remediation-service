from sqlalchemy import desc
from sqlalchemy.orm import Session

from src.config import settings
from src.models.approval import ApprovalModel
from src.models.decision import DecisionModel
from src.models.event import EventModel


class HistoryService:
    def get_history(self, db: Session, project_id: str, environment_id: str, workload_id: str | None = None) -> list[dict]:
        query = db.query(EventModel).filter(
            EventModel.project_id == project_id,
            EventModel.environment_id == environment_id,
        )

        events = query.order_by(desc(EventModel.id)).limit(settings.history_limit).all()

        history: list[dict] = []
        for event in events:
            decision = db.query(DecisionModel).filter(DecisionModel.event_id == event.id).first()
            approval = db.query(ApprovalModel).filter(ApprovalModel.event_id == event.id).first()
            history.append(
                {
                    "event_id": event.id,
                    "signal": event.signal,
                    "decision": decision.action if decision else None,
                    "confidence": decision.confidence if decision else None,
                    "safe_to_auto": decision.final_safe_to_auto if decision else None,
                    "approval_status": approval.status if approval else None,
                    "human_feedback": approval.status if approval and approval.status in {"approved", "rejected"} else None,
                }
            )
        return history
