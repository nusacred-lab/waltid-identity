"""Publish test counts without potentially sensitive JUnit output bodies."""
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET

groups = {
    "cose": (Path("third-party/cose-java/build/test-results/test"), 13),
    "mdoc": (Path("waltid-libraries/credentials/waltid-mdoc-credentials/build/test-results/jvmTest"), 3),
}
summary = {}
for name, (directory, minimum) in groups.items():
    suites = [ET.parse(path).getroot() for path in directory.glob("TEST-*.xml")]
    cases = [case for suite in suites for case in suite.findall("testcase")]
    if len(cases) < minimum:
        raise SystemExit("Required test results are missing: " + name)
    if any(case.find(tag) is not None for case in cases for tag in ("failure", "error", "skipped")):
        raise SystemExit("A required test failed or was skipped: " + name)
    if name == "mdoc":
        required = {"testSigningMdlWithIssuer", "testSigningMdlWithIntermediateIssuer",
                    "testSigningMdlWithOnlyTheIntermediateIssuerCertInX5Chain"}
        actual = {re.split(r"[\[(]", case.attrib["name"])[0] for case in cases}
        if not required <= actual:
            raise SystemExit("Selected mdoc integration cases are missing")
    summary[name] = {"tests": len(cases), "failures": 0, "errors": 0, "skipped": 0}
target = Path("build/baseline-evidence/reports/test-results.json")
target.parent.mkdir(parents=True, exist_ok=True)
target.write_text(json.dumps(summary, indent=2) + "\n")
print("PASS: required COSE and mdoc tests ran without failures or skips")
