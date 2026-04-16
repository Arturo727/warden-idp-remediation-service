import json
import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.db import get_db
from src.domain.schemas import EventIn
from src.domain.validators import validate_context_urls
from src.models.approval import ApprovalModel
from src.models.decision import DecisionModel
from src.models.event import EventModel
from src.models.execution import ExecutionModel
from src.services.event_service import EventService

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Events"])
service = EventService()


@router.post("/webhooks/events", status_code=202, summary="Ingest degradation event")
def ingest_event(payload: EventIn, db: Session = Depends(get_db)) -> dict:
    context_url_errors = validate_context_urls(payload.context)
    if context_url_errors:
        raise HTTPException(status_code=422, detail={"message": "payload validation failed against registered controls", "context_url_errors": context_url_errors})
    try:
        return service.process_event(db, payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("event_processing_failed")
        raise HTTPException(status_code=500, detail="failed to process event") from exc


@router.get("/events", summary="List processed events")
def list_events(db: Session = Depends(get_db)) -> list[dict]:
    events = db.query(EventModel).order_by(EventModel.id.desc()).all()
    return [{"id": e.id, "project_id": e.project_id, "environment_id": e.environment_id, "severity": e.severity, "signal": e.signal, "status": e.status, "timestamp": e.timestamp.isoformat() if e.timestamp else None} for e in events]


@router.get("/events/{event_id}", summary="Get event detail")
def get_event(event_id: int, db: Session = Depends(get_db)) -> dict:
    event = db.query(EventModel).filter(EventModel.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="event not found")

    decision = db.query(DecisionModel).filter(DecisionModel.event_id == event.id).first()
    approval = db.query(ApprovalModel).filter(ApprovalModel.event_id == event.id).first()
    executions = db.query(ExecutionModel).filter(ExecutionModel.event_id == event.id).order_by(ExecutionModel.id.asc()).all()

    api_traces = []
    handler_traces = []

    if decision and decision.llm_prompt_json:
        api_traces.append({
            "api_name": "llm",
            "endpoint": "https://api.groq.com/openai/v1/chat/completions" if decision.llm_provider == "groq" else "local://mock-llm",
            "provider": decision.llm_provider,
            "status": "success" if not decision.llm_error else "fallback",
            "request": json.loads(decision.llm_prompt_json) if decision.llm_prompt_json else None,
            "response": json.loads(decision.llm_response_json) if decision.llm_response_json else None,
            "error": decision.llm_error,
        })
        handler_traces.append({
            "handler_name": "llm_decision_handler",
            "status": "success" if not decision.llm_error else "fallback",
            "action": decision.action,
            "details": {
                "llm_provider": decision.llm_provider,
                "llm_error": decision.llm_error,
            },
        })

    if approval:
        handler_traces.append({
            "handler_name": "approval_request_handler",
            "status": approval.status,
            "action": approval.action,
            "details": {
                "resolved_by": approval.resolved_by,
                "resolution_note": approval.resolution_note,
                "resolved_at": approval.resolved_at.isoformat() if approval.resolved_at else None,
            },
        })

    for ex in executions:
        api_traces.append({
            "api_name": ex.executor_type,
            "endpoint": ex.endpoint,
            "provider": "service",
            "status": ex.status,
            "request": json.loads(ex.request_json) if ex.request_json else None,
            "response": json.loads(ex.response_json) if ex.response_json else None,
            "error": None,
        })
        handler_traces.append({
            "handler_name": ex.executor_type,
            "status": ex.status,
            "action": ex.action,
            "details": {
                "endpoint": ex.endpoint,
            },
        })

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
            "llm_prompt": json.loads(decision.llm_prompt_json) if decision.llm_prompt_json else None,
            "llm_response": json.loads(decision.llm_response_json) if decision.llm_response_json else None,
            "llm_provider": decision.llm_provider,
            "llm_error": decision.llm_error,
        },
        "approval": None if not approval else {
            "id": approval.id,
            "status": approval.status,
            "action": approval.action,
            "approval_message": f"Autorizar acción '{approval.action}' para el evento {approval.event_id}",
            "resolved_by": approval.resolved_by,
            "resolution_note": approval.resolution_note,
            "resolved_at": approval.resolved_at.isoformat() if approval.resolved_at else None,
        },
        "api_traces": api_traces,
        "handler_traces": handler_traces,
    }
