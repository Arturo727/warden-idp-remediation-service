from fastapi import FastAPI

app = FastAPI(
    title="Mock Notifier API",
    version="1.0.0",
    description="Mock notifier used by Warden to simulate on-call notifications.",
)


@app.post("/send", summary="Send notification")
def send(payload: dict) -> dict:
    return {"status": "sent", "payload": payload}
