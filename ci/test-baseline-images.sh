#!/usr/bin/env bash
set -euo pipefail
scanner="$1"
evidence="$PWD/build/baseline-evidence"
private="$(mktemp -d "${RUNNER_TEMP:-/tmp}/api2-harness.XXXXXXXX")"
chmod 700 "$private"
export HARNESS_RUNTIME="$private/runtime"
export HARNESS_REPORT="$evidence/reports/credential-harness.json"
containers=()
images=()
network=''
cleanup() {
  status=$?
  if [[ "$status" -ne 0 ]]; then
    for container in "${containers[@]}"; do
      docker inspect --format 'Runtime state: {{.State.Status}}; exit={{.State.ExitCode}}; oom={{.State.OOMKilled}}' "$container" || true
    done
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
network="$(docker network create "$prefix")"
for service in issuer wallet verifier; do
  case "$service" in issuer) port=7005;; wallet) port=7006;; verifier) port=7004;; esac
  mounts=(--mount "type=bind,source=$HARNESS_RUNTIME/walt/$service,target=/waltid-$service-api2/config,readonly")
  if [[ "$service" == wallet ]]; then
    mounts+=(--mount "type=bind,source=$HARNESS_RUNTIME/data,target=/data")
  fi
  container="$(docker create --network "$network" --network-alias "$service" \
    --cap-drop ALL --security-opt no-new-privileges --memory 2g --pids-limit 512 \
    --read-only --tmpfs /tmp:rw,nosuid,nodev,size=256m \
    --publish "127.0.0.1:$port:$port" "${mounts[@]}" "$prefix-$service")"
  containers+=("$container")
  docker start "$container" >/dev/null
done
python3 ci/harness/wait_ready.py
python3 ci/harness/smoke.py
python3 - "$private" "$evidence" <<'PYTHON'
import hashlib, json, os, pathlib, sys
private, evidence = map(pathlib.Path, sys.argv[1:])
records = []
for service in ("issuer", "wallet", "verifier"):
    image = json.loads((private / (service + "-image.json")).read_text())[0]
    if image["Config"]["Labels"]["org.opencontainers.image.revision"] != os.environ["GITHUB_SHA"]:
        raise SystemExit("Image source revision mismatch")
    if image["Config"]["User"] in ("", "0", "root"):
        raise SystemExit("Image must run without root")
    jar = evidence / "fat-jars" / (service + ".jar")
    records.append({"service": service, "sourceCommit": os.environ["GITHUB_SHA"],
        "localImageConfigDigest": image["Id"], "registryPublished": False,
        "basePlatformManifestDigest": "sha256:da0f0d242bec39e3fe5c1ac4c415840f03be9cef848c243d723166708e02148c",
        "fatJarSha256": hashlib.sha256(jar.read_bytes()).hexdigest()})
(evidence / "reports/images-tested.json").write_text(json.dumps(records, indent=2) + "\n")
PYTHON
