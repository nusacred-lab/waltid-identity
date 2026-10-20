#!/usr/bin/env bash
set -euo pipefail
scanner="$1"
evidence=build/baseline-evidence
mkdir -p "$evidence/reports"
cache="${TRIVY_CACHE_DIR:-${RUNNER_TEMP:-/tmp}/baseline-trivy-cache}"
result=0
for service in issuer wallet verifier; do
  "$scanner" rootfs --cache-dir "$cache" --scanners vuln --format json --exit-code 1 --severity HIGH,CRITICAL \
    --output "$evidence/reports/$service-vulnerabilities.json" "$evidence/runtime/$service" || result=1
  # Generate an inventory covering all severities and all detected runtime JARs.
  "$scanner" rootfs --cache-dir "$cache" --format cyclonedx --output "$evidence/reports/$service-sbom.cdx.json" \
    "$evidence/runtime/$service" || result=1
done
if [[ -f "$cache/db/metadata.json" ]]; then
  cp "$cache/db/metadata.json" "$evidence/reports/trivy-db-metadata.json"
  python3 - "$cache/db/metadata.json" <<'PYTHON'
import datetime, json, sys
updated = datetime.datetime.fromisoformat(json.load(open(sys.argv[1]))["UpdatedAt"].replace("Z", "+00:00"))
assert datetime.timedelta(0) <= datetime.datetime.now(datetime.timezone.utc) - updated < datetime.timedelta(hours=24), "Vulnerability DB must be less than 24 hours old"
PYTHON
else
  result=1
fi
exit "$result"
