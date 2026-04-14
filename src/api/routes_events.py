import json
import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.db import get_db
from src.domain.schemas import EventIn
from src.models.approval import ApprovalModel
from src.models.decision import DecisionModel
from src.models.event import EventModel
from src.services.event_service import EventService

logger = logging.getLogger(__name__)

router = APIRouter(tags=["events"])
service = EventService()


@router.post("/webhooks/events", status_code=202)
def ingest_event(payload: EventIn, db: Session = Depends(get_db)) -> dict:
    try:
        return service.process_event(db, payload)
    except Exception as exc:
        logger.exception("event_processing_failed")
        raise HTTPException(status_code=500, detail="failed to process event") from exc


@router.get("/events")
def list_events(db: Session = Depends(get_db)) -> list[dict]:
    events = db.query(EventModel).order_by(EventModel.id.desc()).all()
    return [
        {
            "id": e.id,
            "project_id": e.project_id,
            "environment_id": e.environment_id,
            "severity": e.severity,
            "signal": e.signal,
            "status": e.status,
            "timestamp": e.timestamp.isoformat() if e.timestamp else None,
        }
        for e in events
    ]


@router.get("/events/{event_id}")
def get_event(event_id: int, db: Session = Depends(get_db)) -> dict:
    event = db.query(EventModel).filter(EventModel.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="event not found")

    decision = db.query(DecisionModel).filter(DecisionModel.event_id == event.id).first()
    approval = db.query(ApprovalModel).filter(ApprovalModel.event_id == event.id).first()

    return {
        "id": event.id,
        "project_id": event.project_id,
        "environment_id": event.environment_id,
        "severity": event.severity,
        "signal": event.signal,
        "context": json.loads(event.context_json),
        "status": event.status,
        "decision": None if not decision else {
            "action": decision.action,
            "confidence": decision.confidence,
            "reasoning": decision.reasoning,
            "llm_safe_to_auto": decision.llm_safe_to_auto,
            "final_safe_to_auto": decision.final_safe_to_auto,
            "restrictions": json.loads(decision.restrictions_applied_json),
        },
        "approval": None if not approval else {
            "id": approval.id,
            "status": approval.status,
            "action": approval.action,
        },
    }
