from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.db import get_db
from src.domain.schemas import ApprovalResolution
from src.models.approval import ApprovalModel
from src.services.approval_service import ApprovalService

router = APIRouter(tags=["approvals"])
service = ApprovalService()


@router.get("/approvals")
def list_approvals(db: Session = Depends(get_db)) -> list[dict]:
    approvals = db.query(ApprovalModel).filter(ApprovalModel.status == "pending").all()
    return [{"id": a.id, "event_id": a.event_id, "action": a.action, "status": a.status} for a in approvals]


@router.post("/approvals/{approval_id}/approve")
def approve(approval_id: int, body: ApprovalResolution, db: Session = Depends(get_db)) -> dict:
    try:
        return service.approve(db, approval_id, body.resolved_by, body.resolution_note)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/approvals/{approval_id}/reject")
def reject(approval_id: int, body: ApprovalResolution, db: Session = Depends(get_db)) -> dict:
    try:
        return service.reject(db, approval_id, body.resolved_by, body.resolution_note)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
