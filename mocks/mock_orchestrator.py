from fastapi import FastAPI

app = FastAPI(
    title="Mock Orchestrator API",
    version="1.0.0",
    description="Mock platform orchestrator used by Warden for rollback, restart and scale-up actions.",
)


@app.post("/rollback", summary="Rollback workload")
def rollback(payload: dict) -> dict:
    return {"status": "success", "action": "rollback", "payload": payload}


@app.post("/restart", summary="Restart workload")
def restart(payload: dict) -> dict:
    return {"status": "success", "action": "restart", "payload": payload}


@app.post("/scale-up", summary="Scale up workload")
def scale_up(payload: dict) -> dict:
    return {"status": "success", "action": "scale_up", "replicas_added": 1, "payload": payload}
