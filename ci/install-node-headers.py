"""Verify Node headers before native builds run without a network."""
import hashlib
import io
import json
from pathlib import Path
import sys
import tarfile
import urllib.request

config = json.loads(Path("ci/tools.json").read_text())["node-headers"]
with urllib.request.urlopen(config["url"], timeout=120) as response:
    payload = response.read()
if hashlib.sha256(payload).hexdigest() != config["sha256"]:
    raise SystemExit("Node headers checksum mismatch")
target = Path(sys.argv[1]).resolve()
target.mkdir(parents=True, exist_ok=False)
with tarfile.open(fileobj=io.BytesIO(payload), mode="r:gz") as archive:
    archive.extractall(target, filter="data")
header = target / ("node-v" + config["version"]) / "include/node/node_version.h"
if not header.is_file():
    raise SystemExit("Unexpected Node headers archive layout")
print("Node headers verified: " + config["version"])
