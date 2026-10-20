#!/usr/bin/env bash
set -euo pipefail
frontend_app="$1"
case "$frontend_app" in
  waltid-credentials|waltid-web-portal2|waltid-digital-credentials) ;;
  *) echo 'Unknown frontend' >&2; exit 2;;
esac
test "$(git rev-parse HEAD)" = "$GITHUB_SHA"
test -z "$(git status --porcelain -- "waltid-applications/$frontend_app")"
python3 ci/verify-npm-review.py
frontend_private="$(mktemp -d "${RUNNER_TEMP:-/tmp}/frontend-${frontend_app}.XXXXXXXX")"
frontend_evidence="$PWD/build/frontend-evidence/$frontend_app"
mkdir -p "$frontend_evidence"
frontend_containers=()
cleanup() {
  for frontend_container in "${frontend_containers[@]}"; do
    docker rm -f "$frontend_container" >/dev/null 2>&1 || true
  done
  rm -rf "$frontend_private"
}
trap cleanup EXIT
python3 - "$frontend_app" "$frontend_private/work" <<'PYTHON'
from pathlib import Path
import shutil, sys
source = Path('waltid-applications') / sys.argv[1]
shutil.copytree(source, sys.argv[2], symlinks=True,
                ignore=shutil.ignore_patterns('node_modules', '.nuxt', '.output', '.data', '.git'))
PYTHON
frontend_builder="$(python3 -c 'import json; print(json.load(open("ci/frontend-toolchain.json"))["builderImage"])')"
run_stage() {
  local frontend_stage="$1" frontend_network="$2" frontend_command="$3"
  local frontend_container frontend_start_status=0
  frontend_container="$(docker create --platform linux/amd64 --network "$frontend_network" \
    --user "$(id -u):$(id -g)" --read-only --cap-drop ALL --security-opt no-new-privileges \
    --memory 4g --cpus 2 --pids-limit 512 --tmpfs /tmp:rw,exec,nosuid,nodev,size=1g \
    --env HOME=/tmp --env CI=true --env FRONTEND_APP="$frontend_app" \
    --env PATH=/npm-tool/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin \
    --env NPM_CONFIG_USERCONFIG=/tmp/empty-user.npmrc --env NPM_CONFIG_GLOBALCONFIG=/tmp/empty-global.npmrc \
    --env npm_config_cache=/tmp/npm-cache --env npm_config_nodedir=/node-headers \
    --env npm_config_build_from_source=true \
    --mount "type=bind,source=$frontend_private/work,target=/work" \
    --mount "type=bind,source=$RUNNER_TEMP/npm-tool,target=/npm-tool,readonly" \
    --mount "type=bind,source=$RUNNER_TEMP/node-headers/node-v22.23.1,target=/node-headers,readonly" \
    --mount "type=bind,source=$PWD/ci/frontend-docs-smoke.mjs,target=/checks/frontend-docs-smoke.mjs,readonly" \
    --mount "type=bind,source=$frontend_evidence,target=/evidence" \
    --workdir /work --entrypoint /bin/sh "$frontend_builder" -ec "$frontend_command")"
  frontend_containers+=("$frontend_container")
  docker start -a "$frontend_container" >"$frontend_private/$frontend_stage.log" 2>&1 || frontend_start_status=$?
  docker inspect --format '{{json .State}}' "$frontend_container" >"$frontend_private/state.json"
  if [[ "$frontend_start_status" -ne 0 ]] || ! python3 -c 'import json,sys; state=json.load(open(sys.argv[1])); sys.exit(0 if state["Status"] == "exited" and state["ExitCode"] == 0 and not state["OOMKilled"] else 1)' "$frontend_private/state.json"; then
    python3 ci/frontend-failure.py "$frontend_stage" "$frontend_private" "$frontend_evidence"
    echo "FAIL: $frontend_app at $frontend_stage; raw package/build output withheld" >&2
    exit 1
  fi
}
# This networked stage runs only the verified package manager, with all package
# lifecycle scripts disabled. Every tarball is covered by the review ledger.
run_stage install bridge '
  test "$(node --version)" = v22.23.1
  test "$(npm --version)" = 11.21.1
  npm ci --ignore-scripts --strict-peer-deps --include=dev --include=optional --no-audit --fund=false --registry=https://registry.npmjs.org
'
# Scripts/native compilation/build/SSR cannot download unreviewed binaries or
# call external services. Native headers were independently verified beforehand.
run_stage build none '
  npm rebuild --offline --foreground-scripts
  npm run build --offline
  if [ "$FRONTEND_APP" = waltid-credentials ]; then
    node /checks/frontend-docs-smoke.mjs
  fi
'
python3 - "$frontend_app" "$frontend_evidence" <<'PYTHON'
import hashlib, json, os, pathlib, sys
app, destination = sys.argv[1:]
toolchain = json.load(open('ci/frontend-toolchain.json'))
lock = pathlib.Path('waltid-applications') / app / 'package-lock.json'
record = dict(schemaVersion=1, app=app, sourceCommit=os.environ['GITHUB_SHA'],
              packageLockSha256=hashlib.sha256(lock.read_bytes()).hexdigest(),
              nodeVersion=toolchain['nodeVersion'], npmVersion=toolchain['npmVersion'],
              builderImage=toolchain['builderImage'], peerValidation='strict',
              lifecycleScriptsDisabledDuringInstall=True, networkDisabledDuringScriptsAndBuild=True,
              build='passed', productionDeployed=False)
(pathlib.Path(destination) / 'build.json').write_text(json.dumps(record, indent=2) + '\n')
PYTHON
echo "PASS: $frontend_app built with reviewed archives and offline lifecycle scripts"
