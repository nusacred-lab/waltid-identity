"""Check the packaged license/provenance and byte-for-byte JAR repeatability."""
import hashlib
import json
from pathlib import Path
import sys
from zipfile import ZipFile

module = Path("third-party/cose-java")
archives = sorted((module / "build/libs").glob("*.jar"))
if len(archives) != 2:
    raise SystemExit("Expected one COSE binary and one sources JAR")
results = {}
for path in archives:
    with ZipFile(path) as archive:
        if archive.read("META-INF/licenses/cose-java/LICENSE") != (module / "LICENSE").read_bytes():
            raise SystemExit("COSE license missing or changed")
        if archive.read("META-INF/nusacred/cose-java/upstream-source.json") != (module / "upstream-source.json").read_bytes():
            raise SystemExit("COSE source provenance missing or changed")
        if not path.name.endswith("-sources.jar"):
            classes = [n for n in archive.namelist() if n.endswith(".class")]
            if not classes or any(int.from_bytes(archive.read(n)[6:8], "big") != 61 for n in classes):
                raise SystemExit("Expected Java 17 bytecode for every COSE class")
    results[path.name] = hashlib.sha256(path.read_bytes()).hexdigest()
record = module / "build/cose-reproducibility.json"
if sys.argv[1] == "record":
    record.write_text(json.dumps({"first_build": results}, indent=2) + "\n")
elif sys.argv[1] == "compare":
    prior = json.loads(record.read_text())
    if prior["first_build"] != results:
        raise SystemExit("COSE JARs are not byte-for-byte repeatable")
    prior.update({"second_build": results, "reproducible": True})
    record.write_text(json.dumps(prior, indent=2) + "\n")
    print("PASS: both COSE JARs repeat byte-for-byte and include license/provenance")
else:
    raise SystemExit("Expected record or compare")
