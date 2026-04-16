from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.db import get_db
from src.domain.schemas import ApprovalResolution
from src.models.approval import ApprovalModel
from src.services.approval_service import ApprovalService

router = APIRouter(tags=["Approvals"])
service = ApprovalService()


@router.get("/approvals", summary="List pending approvals")
def list_approvals(db: Session = Depends(get_db)) -> list[dict]:
    approvals = db.query(ApprovalModel).filter(ApprovalModel.status == "pending").all()
    return [
        {
            "id": a.id,
            "event_id": a.event_id,
            "action": a.action,
            "status": a.status,
            "resolved_by": a.resolved_by,
            "resolution_note": a.resolution_note,
            "approval_message": f"Autorizar acción '{a.action}' para el evento {a.event_id}",
        }
        for a in approvals
    ]


@router.post("/approvals/{approval_id}/approve", summary="Approve pending action")
def approve(approval_id: int, body: ApprovalResolution, db: Session = Depends(get_db)) -> dict:
    try:
        return service.approve(db, approval_id, body.resolved_by, body.resolution_note)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/approvals/{approval_id}/reject", summary="Reject pending action")
def reject(approval_id: int, body: ApprovalResolution, db: Session = Depends(get_db)) -> dict:
    try:
        return service.reject(db, approval_id, body.resolved_by, body.resolution_note)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
