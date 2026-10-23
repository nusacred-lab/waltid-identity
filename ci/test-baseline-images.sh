#!/usr/bin/env bash
set -euo pipefail
scanner="$1"
evidence="$PWD/build/baseline-evidence"
private="$(mktemp -d "${RUNNER_TEMP:-/tmp}/api2-harness.XXXXXXXX")"
chmod 700 "$private"
export HARNESS_RUNTIME="$private/runtime"
export HARNESS_PREPARATION_REPORT="$evidence/reports/demo-key-preparation.json"
containers=()
images=()
network=''
cleanup() {
  status=$?
  if [[ "$status" -ne 0 ]]; then
    for container in "${containers[@]}"; do
      docker inspect --format 'Runtime state: {{.State.Status}}; exit={{.State.ExitCode}}; oom={{.State.OOMKilled}}' "$container" || true
      docker logs "$container" >"$private/$container.log" 2>&1 || true
    done
    python3 ci/harness/startup-diagnostics.py "$private" "$evidence/reports" || true
  fi
  for container in "${containers[@]}"; do docker rm -f "$container" >/dev/null 2>&1 || true; done
  if [[ -n "$network" ]]; then docker network rm "$network" >/dev/null 2>&1 || true; fi
  for image in "${images[@]}"; do docker image rm "$image" >/dev/null 2>&1 || true; done
  rm -rf "$private"
}
trap cleanup EXIT
test "$(id -u)" -ne 0
test "${GITHUB_SHA:-}" != ''
python3 ci/harness/prepare.py
mkdir -m 700 "$HARNESS_RUNTIME/data"
prefix="baseline-${GITHUB_RUN_ID:-local}-${GITHUB_RUN_ATTEMPT:-1}"
cache="${TRIVY_CACHE_DIR:-${RUNNER_TEMP:-/tmp}/baseline-trivy-cache}"
for service in issuer wallet verifier; do
  image="$prefix-$service"
  # The context contains only the three previously hashed fat JARs.
  images+=("$image")
  docker build --platform linux/amd64 --file ci/Dockerfile.api2 \
    --build-arg "SERVICE=$service" --build-arg "RUNTIME_UID=$(id -u)" \
    --build-arg "SOURCE_REVISION=$GITHUB_SHA" --tag "$image" "$evidence/fat-jars" \
    >"$private/$service-build.log" 2>&1
  docker image inspect "$image" >"$private/$service-image.json"
  "$scanner" image --image-src docker --cache-dir "$cache" --scanners vuln \
    --format json --severity HIGH,CRITICAL --exit-code 1 \
    --output "$evidence/reports/$service-image-vulnerabilities.json" "$image"
  "$scanner" image --image-src docker --cache-dir "$cache" --format cyclonedx \
    --output "$evidence/reports/$service-image-sbom.cdx.json" "$image"
done
network="$(docker network create --internal "$prefix")"
docker network inspect "$network" >"$private/network.json"
for service in issuer wallet verifier; do
  temporary_options=rw,noexec,nosuid,nodev,size=256m
  mounts=(--mount "type=bind,source=$HARNESS_RUNTIME/walt/$service,target=/waltid-$service-api2/config,readonly")
  if [[ "$service" == wallet ]]; then
    # SQLite JDBC extracts/loads its verified native library from java.io.tmpdir.
    temporary_options=rw,exec,nosuid,nodev,size=256m
    mounts+=(--mount "type=bind,source=$HARNESS_RUNTIME/data,target=/data")
  fi
  container="$(docker create --network "$network" --network-alias "$service" \
    --dns 127.0.0.1 --cap-drop ALL --security-opt no-new-privileges --memory 2g --pids-limit 512 \
    --read-only --tmpfs "/tmp:$temporary_options" \
    "${mounts[@]}" "$prefix-$service")"
  containers+=("$container")
  docker start "$container" >/dev/null
  docker inspect "$container" >"$private/$service-container.json"
done
# The Python runner joins the same internal bridge; there are no host ports,
# upstream key mounts, host homes or external DNS resolvers.
runner_image="$(python3 -c 'import json; print(json.load(open("ci/frontend-toolchain.json"))["builderImage"])')"
runner="$(docker create --platform linux/amd64 --network "$network" --dns 127.0.0.1 \
  --user "$(id -u):$(id -g)" --read-only --cap-drop ALL --security-opt no-new-privileges \
  --memory 256m --pids-limit 128 --tmpfs /tmp:rw,noexec,nosuid,nodev,size=32m \
  --env PYTHONDONTWRITEBYTECODE=1 --env HOME=/tmp --env NO_PROXY='*' \
  --env HTTP_PROXY= --env HTTPS_PROXY= --env ALL_PROXY= \
  --env http_proxy= --env https_proxy= --env all_proxy= \
  --env ISSUER_URL=http://issuer:7005 --env WALLET_URL=http://wallet:7006 --env VERIFIER_URL=http://verifier:7004 \
  --env HARNESS_REPORT=/reports/credential-harness.json \
  --env HARNESS_ISOLATION_REPORT=/reports/demo-isolation.json \
  --mount "type=bind,source=$PWD/ci/harness,target=/checks,readonly" \
  --mount "type=bind,source=$evidence/reports,target=/reports" \
  --entrypoint /bin/sh "$runner_image" -ec \
  'python3 /checks/check_isolation.py && python3 /checks/wait_ready.py && python3 /checks/smoke.py')"
containers+=("$runner")
if ! docker start -a "$runner" >"$private/harness-runner.log" 2>&1; then
  echo 'FAIL: internal real HTTP harness; raw protocol output withheld' >&2
  exit 1
fi
docker inspect "$runner" >"$private/runner-container.json"
python3 ci/harness/check_container_isolation.py "$private" "$evidence/reports"
python3 ci/harness/test-isolation-rejection.py "$private" "$evidence/reports"

python3 - "$private" "$evidence" <<'PYTHON'
import hashlib, json, os, pathlib, sys
private, evidence = map(pathlib.Path, sys.argv[1:])
records = []
for service in ("issuer", "wallet", "verifier"):
    image = json.loads((private / (service + "-image.json")).read_text())[0]
    if image["Config"]["Labels"]["org.opencontainers.image.revision"] != os.environ["GITHUB_SHA"]:
        raise SystemExit("Image source revision mismatch")
    if image["Config"]["Labels"].get("org.nusacred.scope") != "synthetic-isolated-demo-only":
        raise SystemExit("Demo image scope label missing")
    if image["Config"]["User"] in ("", "0", "root"):
        raise SystemExit("Image must run without root")
    jar = evidence / "fat-jars" / (service + ".jar")
    records.append({"service": service, "sourceCommit": os.environ["GITHUB_SHA"],
        "localImageConfigDigest": image["Id"], "registryPublished": False,
        "scope": "synthetic-isolated-demo-only", "productionEligible": False,
        "baseRuntimeImage": "ghcr.io/nusacred-lab/competency-proof-jvm-runtime@sha256:ecbcd98b260eac22078f57b46422999409094325a44d5f12e2f0b8ac6de90a89",
        "fatJarSha256": hashlib.sha256(jar.read_bytes()).hexdigest()})
(evidence / "reports/images-tested.json").write_text(json.dumps(records, indent=2) + "\n")
PYTHON
