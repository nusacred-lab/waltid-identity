"""Bind the resolved runtime inventory, JAR bytes and attribution to a CycloneDX SBOM."""
import datetime
import hashlib
import json
import re
from pathlib import Path
from urllib.parse import quote
from uuid import uuid4
from zipfile import ZipFile

def require(condition, message):
    if not condition:
        raise SystemExit(message)

def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()

base = Path("build/baseline-evidence")
licenses = Path("ci/licenses/kotlinx-serialization")
provenance = json.loads((licenses / "provenance.json").read_text())
require(provenance["commit"] == "4fe61aca0dd185b0cdb920a050df81dab121cae9", "Runtime evidence invariant failed")
require(set(provenance["files"]) == {"LICENSE.txt", "WALTID-FORK-NOTICE.md", "license/LICENSE.txt", "license/NOTICE.txt"}, "Incomplete serialization attribution manifest")
for name, expected in provenance["files"].items():
    require(digest(licenses / name) == expected, name)

for service in ("issuer", "wallet", "verifier"):
    manifest = json.loads((base / f"{service}-runtime.json").read_text())
    revision = manifest["workflowSourceSha"]
    require(revision and re.fullmatch(r"[0-9a-f]{40}", revision), "A source commit is required")
    require(len(manifest["fatJars"]) == 1 and manifest["runtimeArtifacts"], "Runtime evidence invariant failed")
    fat_jar = base / "fat-jars" / manifest["fatJars"][0]["file"]
    require(digest(fat_jar) == manifest["fatJars"][0]["sha256"], "Runtime evidence invariant failed")
    with ZipFile(fat_jar) as archive:
        for path in licenses.rglob("*"):
            if path.is_file():
                require(archive.read("META-INF/licenses/waltid-kotlinx-serialization/" + str(path.relative_to(licenses))) == path.read_bytes(), "Runtime evidence invariant failed")
        require(archive.read("META-INF/licenses/cose-java/LICENSE") == Path("third-party/cose-java/LICENSE").read_bytes(), "Runtime evidence invariant failed")
    components = []
    for artifact in manifest["runtimeArtifacts"]:
        jar = base / "runtime" / service / (artifact["sha256"] + "-" + artifact["file"])
        require(digest(jar) == artifact["sha256"], artifact["file"])
        identity = artifact["component"]
        fields = identity.split(":")
        component = {"type": "library", "hashes": [{"alg": "SHA-256", "content": artifact["sha256"]}]}
        if len(fields) == 3 and " " not in fields[0]:
            group, name, version = fields
            purl = "pkg:maven/" + quote(group, safe=".") + "/" + quote(name, safe="") + "@" + quote(version, safe="")
            component.update(group=group, name=name, version=version, purl=purl)
        elif identity.startswith("project "):
            component.update(group="nusacred.source", name=identity.removeprefix("project "), version=revision,
                externalReferences=[{"type": "vcs", "url": "https://github.com/nusacred-lab/waltid-identity/tree/" + revision}])
            purl = "source:" + identity
        else:
            raise ValueError("Unidentified runtime artifact: " + identity)
        component["bom-ref"] = purl + "#" + artifact["sha256"]
        components.append(component)
    declared_files = {a["sha256"] + "-" + a["file"] for a in manifest["runtimeArtifacts"]}
    actual_files = {p.name for p in (base / "runtime" / service).iterdir() if p.is_file()}
    require(declared_files == actual_files, "Unrecorded or missing runtime artifact: " + service)
    root_ref = "api2:" + service + ":" + revision
    document = {"bomFormat": "CycloneDX", "specVersion": "1.6", "serialNumber": "urn:uuid:" + str(uuid4()), "version": 1,
        "metadata": {"timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "component": {"type": "application", "name": "waltid-" + service + "-api2", "version": revision,
                "bom-ref": root_ref, "hashes": [{"alg": "SHA-256", "content": manifest["fatJars"][0]["sha256"]}]}},
        "components": components,
        "dependencies": [{"ref": root_ref, "dependsOn": [c["bom-ref"] for c in components]}]}
    target = base / "reports" / (service + "-resolved-sbom.cdx.json")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(document, indent=2) + "\n")
    print(f"PASS: {service}: {len(components)} runtime artifacts bound to JAR bytes and source; licenses packaged")
