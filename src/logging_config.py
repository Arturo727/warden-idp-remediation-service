import json
import logging
import os
from logging.handlers import RotatingFileHandler
from pathlib import Path

class JsonFormatter(logging.Formatter):
    def format(self, record):
        payload = {
            "asctime": self.formatTime(record, self.datefmt),
            "levelname": record.levelname,
            "name": record.name,
            "message": record.getMessage(),
        }
        skip = {
            "name","msg","args","levelname","levelno","pathname","filename","module",
            "exc_info","exc_text","stack_info","lineno","funcName","created","msecs",
            "relativeCreated","thread","threadName","processName","process","message","asctime"
        }
        for key, value in record.__dict__.items():
            if key.startswith("_") or key in skip:
                continue
            try:
                json.dumps(value)
                payload[key] = value
            except Exception:
                payload[key] = str(value)
        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False)

def setup_logging():
    logs_dir = Path(os.getenv("LOG_DIR", "./logs"))
    logs_dir.mkdir(parents=True, exist_ok=True)
    formatter = JsonFormatter()

    root = logging.getLogger()
    root.setLevel(logging.INFO)
    root.handlers.clear()

    sh = logging.StreamHandler()
    sh.setFormatter(formatter)
    root.addHandler(sh)

    fh = RotatingFileHandler(
        logs_dir / "warden.jsonl",
        maxBytes=2_000_000,
        backupCount=5,
        encoding="utf-8",
    )
    fh.setFormatter(formatter)
    root.addHandler(fh)
