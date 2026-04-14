from sqlalchemy import Column, DateTime, Integer, String, Text
from sqlalchemy.sql import func

from src.db import Base


class EventModel(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(String, nullable=False, index=True)
    environment_id = Column(String, nullable=False, index=True)
    severity = Column(String, nullable=False)
    signal = Column(Text, nullable=False)
    context_json = Column(Text, nullable=False, default="{}")
    timestamp = Column(DateTime(timezone=True), nullable=False)
    status = Column(String, nullable=False, default="received")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
