"""Install the reviewed npm release in an otherwise empty temporary directory."""
import hashlib
import io
import json
from pathlib import Path
import sys
import tarfile
import urllib.request

config = json.loads(Path("ci/tools.json").read_text())["npm"]
with urllib.request.urlopen(config["url"], timeout=120) as response:
    payload = response.read()
if hashlib.sha256(payload).hexdigest() != config["sha256"]:
    raise SystemExit("npm archive checksum mismatch")
target = Path(sys.argv[1]).resolve()
target.mkdir(parents=True, exist_ok=False)
with tarfile.open(fileobj=io.BytesIO(payload), mode="r:gz") as archive:
    archive.extractall(target, filter="data")
if json.loads((target / "package/package.json").read_text())["version"] != config["version"]:
    raise SystemExit("npm archive version mismatch")
binary_dir = target / "bin"
binary_dir.mkdir()
for name in ("npm", "npx"):
    wrapper = binary_dir / name
    wrapper.write_text("#!/usr/bin/env node\nrequire('../package/bin/" + name + "-cli.js')\n")
    wrapper.chmod(0o755)
print("npm archive verified: " + config["version"])
