"""Verify the exact vendored upstream source set before running any build."""
import hashlib
import json
from pathlib import Path
import sys


def verify(root):
    manifest = json.loads((root / "upstream-source.json").read_text())
    if manifest["upstream_commit"] != "fc897fa9da31f35c5f2e3e092496ad1c57e10457":
        raise SystemExit("Unexpected COSE source revision")
    expected = {item["path"]: item["sha256"] for item in manifest["files"]}
    actual = {str(p.relative_to(root)) for p in (root / "src/main/java").rglob("*") if p.is_file()}
    if actual != set(expected) - {"LICENSE"} or len(actual) != 24:
        raise SystemExit("COSE upstream file set changed; explicit source review required")
    for name, checksum in expected.items():
        if hashlib.sha256((root / name).read_bytes()).hexdigest() != checksum:
            raise SystemExit("COSE upstream content changed: " + name)
    print("PASS: 24 COSE Java sources and upstream LICENSE match the pinned manifest")


if __name__ == "__main__":
    verify(Path(sys.argv[1]) if len(sys.argv) > 1 else Path("third-party/cose-java"))
