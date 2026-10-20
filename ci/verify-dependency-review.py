"""Fail closed if verification hashes or lockfiles differ from the reviewed ledger."""
import hashlib
import json
from pathlib import Path
import sys
from urllib.parse import urlparse
import xml.etree.ElementTree as ET

def require(condition, message):
    if not condition:
        raise SystemExit(message)

root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
metadata = root / "gradle/verification-metadata.xml"
ledger_path = root / "ci/dependency-review.json"
ledger = json.loads(ledger_path.read_text())
require(hashlib.sha256(metadata.read_bytes()).hexdigest() == ledger["metadataSha256"], "Verification metadata changed without review")
ns = {"v": "https://schema.gradle.org/dependency-verification"}
tree = ET.parse(metadata)
require(tree.findtext("v:configuration/v:verify-metadata", namespaces=ns) == "true", "Runtime evidence invariant failed")
for forbidden in ("trusted-artifacts", "ignored-artifacts", "trusted-keys"):
    require(not tree.findall(".//v:" + forbidden, ns), "Broad trust/ignore rules are not accepted")
expected = {}
for component in tree.findall(".//v:component", ns):
    require("SNAPSHOT" not in component.attrib["version"], "Runtime evidence invariant failed")
    for artifact in component.findall("v:artifact", ns):
        hashes = artifact.findall("v:sha256", ns)
        require(len(hashes) == 1, "Runtime evidence invariant failed")
        key = (component.attrib["group"], component.attrib["name"], component.attrib["version"], artifact.attrib["name"])
        require(key not in expected, "Runtime evidence invariant failed")
        expected[key] = hashes[0].attrib["value"]
reviewed = {}
methods = {"published-sha256", "download-sha256", "mapped-download-sha256", "publisher-release-source-reviewed", "official-release-asset-digest"}
hosts = {"repo.maven.apache.org", "dl.google.com", "plugins.gradle.org", "maven.waltid.dev", "github.com"}
for entry in ledger["artifacts"]:
    key = (entry["group"], entry["name"], entry["version"], entry["artifact"])
    require(key not in reviewed, "Runtime evidence invariant failed")
    require(entry["method"] in methods, "Runtime evidence invariant failed")
    source = urlparse(entry["source"])
    require(source.scheme == "https" and source.hostname in hosts, "Runtime evidence invariant failed")
    if source.hostname == "maven.waltid.dev":
        require(entry["version"] == "1.11.1-waltid-20260811" and entry["group"] == "org.jetbrains.kotlinx", "Runtime evidence invariant failed")
        require(entry["sourceCommit"] == "4fe61aca0dd185b0cdb920a050df81dab121cae9", "Runtime evidence invariant failed")
    if source.hostname == "github.com":
        require(source.path.startswith("/JetBrains/kotlin/releases/"), "Runtime evidence invariant failed")
    reviewed[key] = entry["sha256"]
require(reviewed == expected, "Every metadata hash must have an exact review entry")
for name, expected_hash in ledger["lockfiles"].items():
    path = Path(name)
    require(not path.is_absolute() and ".." not in path.parts, "Runtime evidence invariant failed")
    require(hashlib.sha256((root / path).read_bytes()).hexdigest() == expected_hash, "Lockfile changed: " + name)
print(f"PASS: {len(reviewed)} reviewed verification hashes and {len(ledger['lockfiles'])} lockfiles match")
