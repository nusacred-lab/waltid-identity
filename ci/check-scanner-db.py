"""Reject missing, stale or future-dated vulnerability databases."""
import datetime
import json
import sys
from pathlib import Path

metadata = json.loads(Path(sys.argv[1]).read_text())
updated = datetime.datetime.fromisoformat(metadata["UpdatedAt"].replace("Z", "+00:00"))
age = datetime.datetime.now(datetime.timezone.utc) - updated
if not datetime.timedelta(0) <= age < datetime.timedelta(hours=24):
    raise SystemExit("Vulnerability database must be less than 24 hours old")
print("PASS: vulnerability database is less than 24 hours old")
