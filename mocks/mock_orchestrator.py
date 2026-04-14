from fastapi import FastAPI

app = FastAPI(title="Mock Orchestrator")


@app.post("/rollback")
def rollback(payload: dict) -> dict:
    return {"status": "success", "action": "rollback", "payload": payload}


@app.post("/restart")
def restart(payload: dict) -> dict:
    return {"status": "success", "action": "restart", "payload": payload}


@app.post("/scale-up")
def scale_up(payload: dict) -> dict:
    return {"status": "success", "action": "scale_up", "replicas_added": 1, "payload": payload}
