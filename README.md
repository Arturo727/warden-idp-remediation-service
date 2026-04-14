# Warden

Warden is an internal IDP service that receives degradation events from observability platforms, reasons about them with an LLM, applies deterministic safety guardrails, and either executes a remediation or routes the case to human approval.

This implementation is designed for the technical assessment and focuses on:
- clear separation of concerns
- deterministic policy enforcement over LLM output
- human-in-the-loop approvals
- local execution with Docker Compose
- automated tests for the main flows

## High-level flow

1. Observability sends a webhook event to `POST /webhooks/events`.
2. Warden validates and stores the event.
3. Warden retrieves the latest N historical events for the same workload scope.
4. Warden asks the LLM for a structured recommendation.
5. Warden applies deterministic safety rules:
   - `critical` severity always disables auto-execution
   - confidence below threshold disables auto-execution
   - `prod` + `rollback` or `scale_up` disables auto-execution
6. If auto-execution is allowed, Warden invokes the mocked platform orchestrator.
7. Otherwise, Warden creates an approval request and notifies the mocked on-call channel.
8. Human approval or rejection is stored as feedback for future reasoning.

## Architecture

```text
Observability Webhook
        |
        v
   FastAPI API
        |
        v
   Event Service
   |          |
   |          +--> History Service --> SQLite
   |
   +--> Reasoning Service --> LLM Client (mock or Groq)
   |
   +--> Safety Rules / Guardrails
   |
   +--> Action Service
            |               |
            v               v
   Mock Orchestrator   Mock Notifier
```

## Tech stack

- Python 3.12
- FastAPI
- SQLAlchemy
- SQLite
- Docker / Docker Compose
- Pytest
- Optional Groq integration via API key

## Project structure

```text
warden_final/
├── README.md
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── .env.example
├── .gitignore
├── src/
├── mocks/
└── tests/
```

## Run locally

```bash
cp .env.example .env
docker compose up --build
```

Service endpoints:
- Warden: `http://localhost:8000`
- Mock orchestrator: `http://localhost:8001`
- Mock notifier: `http://localhost:8002`

## API

- `GET /health`
- `POST /webhooks/events`
- `GET /events`
- `GET /events/{id}`
- `GET /approvals`
- `POST /approvals/{id}/approve`
- `POST /approvals/{id}/reject`

## Example request

```bash
curl -X POST http://localhost:8000/webhooks/events \
  -H "Content-Type: application/json" \
  -d '{
    "project_id": "payments-api",
    "environment_id": "prod",
    "severity": "high",
    "signal": "P99 latency spiked to 4s after the 14:30 deploy",
    "context": {
      "last_deploy": "v2.3.1",
      "cpu_usage": "85%",
      "error_rate": "12%",
      "workload_id": "payments-api"
    },
    "timestamp": "2024-04-03T14:45:00Z"
  }'
```

## Example approval

```bash
curl -X POST http://localhost:8000/approvals/1/approve \
  -H "Content-Type: application/json" \
  -d '{
    "resolved_by": "human-on-call",
    "resolution_note": "Approved after reviewing the incident context"
  }'
```

## Tests

Local:
```bash
pip install -r requirements.txt
pytest -q
```

With coverage:
```bash
pytest --cov=src --cov-report=term-missing
```

## Configuration

Environment variables:

- `APP_NAME`
- `APP_ENV`
- `APP_PORT`
- `DATABASE_URL`
- `LLM_MODE` → `mock` or `groq`
- `GROQ_API_KEY`
- `GROQ_MODEL`
- `HISTORY_LIMIT`
- `CONFIDENCE_THRESHOLD`
- `ORCHESTRATOR_URL`
- `NOTIFIER_URL`

## Design decisions

### 1. LLM output is advisory, not authoritative
The LLM proposes a remediation, but Warden always applies deterministic rules before auto-executing any action.

### 2. History is included before reasoning
Warden enriches the prompt with the latest N events for the same workload scope so the LLM can see prior signals, decisions, and human feedback.

### 3. Human approval is persisted
Approval requests remain stored until they are approved or rejected. Their outcome is later visible to the LLM as feedback context.

### 4. External systems are mocked
The platform orchestrator and notifier are intentionally mocked because the exercise explicitly requires it.

### 5. Simple persistence for local execution
SQLite was chosen to keep the project easy to run with a single command while still preserving approvals, events, decisions, executions, and feedback.

## Assumptions

- The contract does not expose a first-class `workload_id`. For that reason, the history scope uses `project_id + environment_id`, with optional support for `context.workload_id`.
- Processing is synchronous in this assessment implementation to keep the flow simple and easy to validate locally.
- Authentication is out of scope for the exercise.

## Possible next improvements

- asynchronous processing with a queue
- idempotency keys for duplicate webhook events
- authentication / request signing for inbound webhooks
- OpenTelemetry tracing
- PostgreSQL for multi-user scenarios
- richer policy engine for safety constraints
- real Slack / PagerDuty / orchestrator integrations
