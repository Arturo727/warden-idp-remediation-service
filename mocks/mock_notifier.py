from fastapi import FastAPI

app = FastAPI(title="Mock Notifier")


@app.post("/send")
def send(payload: dict) -> dict:
    return {"status": "sent", "payload": payload}
