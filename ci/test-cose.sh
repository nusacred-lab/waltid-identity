#!/usr/bin/env bash
set -euo pipefail
mode="${1:-verify}"
module=third-party/cose-java
args=(-p "$module" --no-daemon --no-configuration-cache -Dorg.gradle.jvmargs=-Xmx1g)
if [[ "$mode" == bootstrap || "$mode" == cose-bootstrap ]]; then
  args+=(--write-locks --write-verification-metadata sha256)
elif [[ "$mode" == verify ]]; then
  test -s "$module/gradle.lockfile"
  test -s "$module/gradle/verification-metadata.xml"
  args+=(--dependency-verification strict)
else
  echo 'Expected verify, bootstrap or cose-bootstrap' >&2; exit 2
fi
python3 ci/verify-cose-source.py
./gradlew "${args[@]}" clean check jar sourcesJar
python3 ci/check-cose-jar.py record
# This is a repeatability check, not automatic approval of bootstrap checksums.
./gradlew -p "$module" --no-daemon --no-configuration-cache -Dorg.gradle.jvmargs=-Xmx1g \
  --dependency-verification strict --rerun-tasks --no-build-cache jar sourcesJar
python3 ci/check-cose-jar.py compare
