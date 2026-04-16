from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.sql import func

from src.db import Base


class DecisionModel(Base):
    __tablename__ = "decisions"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey("events.id"), nullable=False, index=True)
    action = Column(String, nullable=False)
    confidence = Column(Float, nullable=False)
    reasoning = Column(Text, nullable=False)
    llm_safe_to_auto = Column(Boolean, nullable=False)
    final_safe_to_auto = Column(Boolean, nullable=False)
    restrictions_applied_json = Column(Text, nullable=False, default="[]")
    llm_prompt_json = Column(Text, nullable=True)
    llm_response_json = Column(Text, nullable=True)
    llm_provider = Column(String, nullable=True)
    llm_error = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
