from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.sql import func

from src.db import Base


class ExecutionModel(Base):
    __tablename__ = "executions"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey("events.id"), nullable=False, index=True)
    action = Column(String, nullable=False)
    executor_type = Column(String, nullable=False)
    status = Column(String, nullable=False)
    result_json = Column(Text, nullable=False, default="{}")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
