#!/usr/bin/env bash
set -euo pipefail

output="$GITHUB_WORKSPACE/native-bootstrap"
phase="$GITHUB_WORKSPACE/waltid-identity/.github/scripts/mobile-ci/run-ios-phase.py"
mkdir -p "$output"
xcrun simctl list devices available --json > "$output/devices-before.json"
simulator=$(python3 - "$output/devices-before.json" <<'PY'
import json, sys
devices = json.load(open(sys.argv[1]))['devices']['com.apple.CoreSimulator.SimRuntime.iOS-27-0']
matches = [d for d in devices if d['name'] == 'iPhone 17']
assert len(matches) == 1, matches
print(matches[0]['udid'])
PY
)
sampler=''
cleanup() {
  status=$?
  if [[ -n "$sampler" ]]; then
    kill "$sampler" 2>/dev/null || true
    wait "$sampler" 2>/dev/null || true
  fi
  xcrun simctl shutdown "$simulator" 2>/dev/null || true
  exit "$status"
}
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

cd "$GITHUB_WORKSPACE/waltid-identity/waltid-applications/waltid-wallet-demo-ios/iosApp"
failures=0
for iteration in 1 2 3; do
  attempt="$output/attempt-$iteration"
  mkdir -p "$attempt"
  (
    while true; do
      date -u '+%Y-%m-%dT%H:%M:%SZ'
      vm_stat
      ps -A -o pid,ppid,pcpu,pmem,rss,comm | sort -nrk3 | head -25 || true
      sleep 5
    done
  ) > "$attempt/resources.log" 2>&1 &
  sampler=$!
  if [[ "$WAIT_FOR_BOOT" == true ]]; then
    python3 "$phase" --output-dir "$attempt" boot xcrun simctl bootstatus "$simulator" -b
  fi
  if ! python3 "$phase" --output-dir "$attempt" native \
    xcodebuild test -collect-test-diagnostics on-failure \
    -project iosApp.xcodeproj -scheme iosApp -configuration Debug \
    -destination "platform=iOS Simulator,id=$simulator" \
    -only-testing:iosAppUITests/MockWalletUITests/testExternalOfferFromSettingsOpensOneTaskAndClosesToHome \
    -resultBundlePath "$attempt/TestResults.xcresult" -derivedDataPath /tmp/xcode-derived \
    -enableCodeCoverage NO -parallel-testing-enabled NO OVERRIDE_KOTLIN_BUILD_IDE_SUPPORTED=YES; then
    failures=$((failures + 1))
  fi
  kill "$sampler" 2>/dev/null || true
  wait "$sampler" 2>/dev/null || true
  sampler=''
  xcrun xcresulttool get test-results summary --path "$attempt/TestResults.xcresult" > "$attempt/summary.json"
  xcrun xcresulttool export diagnostics --path "$attempt/TestResults.xcresult" --output-path "$attempt/diagnostics"
  xcrun simctl shutdown "$simulator"
done
python3 - "$output" <<'PY'
import json, pathlib, sys
root = pathlib.Path(sys.argv[1])
for iteration in range(1, 4):
    data = json.loads((root / f'attempt-{iteration}' / 'summary.json').read_text())
    assert data['totalTestCount'] == 1 and data['passedTests'] == 1, data
PY
(( failures == 0 ))
