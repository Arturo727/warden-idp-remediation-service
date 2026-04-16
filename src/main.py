from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.routes_approvals import router as approvals_router
from src.api.routes_events import router as events_router
from src.api.routes_meta import router as meta_router
from src.api.routes_health import router as health_router
from src.db import Base, engine
from src.logging_config import setup_logging

setup_logging()
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Warden API",
    version="1.2.0",
    description=(
        "Warden receives degradation events, reasons over them with an LLM, "
        "applies deterministic safety guardrails, and either executes a remediation "
        "or creates a human approval request."
    ),
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    contact={"name": "Warden Technical Assessment"},
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:4173",
        "http://127.0.0.1:4173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(events_router)
app.include_router(meta_router)
app.include_router(approvals_router)
