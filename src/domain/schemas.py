from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field, field_validator

from src.domain.enums import Action, Severity


class EventIn(BaseModel):
    project_id: str = Field(..., min_length=1)
    environment_id: str = Field(..., min_length=1)
    severity: Severity
    signal: str = Field(..., min_length=1)
    context: dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime

    @field_validator("context")
    @classmethod
    def validate_context(cls, value: dict[str, Any]) -> dict[str, Any]:
        if not isinstance(value, dict):
            raise ValueError("context must be an object")
        return value


class DecisionOut(BaseModel):
    action: Action
    confidence: float = Field(..., ge=0.0, le=1.0)
    reasoning: str
    safe_to_auto: bool


class ApprovalResolution(BaseModel):
    resolution_note: Optional[str] = None
    resolved_by: str = "human-on-call"
