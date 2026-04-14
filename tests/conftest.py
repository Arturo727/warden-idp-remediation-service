import os
from pathlib import Path

os.environ["DATABASE_URL"] = "sqlite:///./test_warden.db"

test_db = Path("test_warden.db")
if test_db.exists():
    test_db.unlink()
