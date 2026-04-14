from enum import Enum


class Severity(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class Action(str, Enum):
    rollback = "rollback"
    restart = "restart"
    scale_up = "scale_up"
    notify_human = "notify_human"
    no_action = "no_action"


class EventStatus(str, Enum):
    received = "received"
    awaiting_approval = "awaiting_approval"
    executed = "executed"
    rejected = "rejected"
    failed = "failed"


class ApprovalStatus(str, Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"
