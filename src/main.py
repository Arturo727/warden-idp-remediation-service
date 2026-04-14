from fastapi import FastAPI

from src.api.routes_approvals import router as approvals_router
from src.api.routes_events import router as events_router
from src.api.routes_health import router as health_router
from src.db import Base, engine
from src.logging_config import setup_logging

setup_logging()
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Warden", version="1.0.0")

app.include_router(health_router)
app.include_router(events_router)
app.include_router(approvals_router)
