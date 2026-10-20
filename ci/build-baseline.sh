#!/usr/bin/env bash
set -euo pipefail
mode="${1:-verify}"
args=(--no-daemon --no-configuration-cache --max-workers=2 -Dorg.gradle.jvmargs=-Xmx6g -I ci/locking.init.gradle)
if [[ "$mode" == bootstrap ]]; then
  args+=(-Pp1Bootstrap=true --write-locks --write-verification-metadata sha256)
elif [[ "$mode" == verify ]]; then
  test -s gradle/verification-metadata.xml
  test -s build-logic/gradle.lockfile
  args+=(--dependency-verification strict)
else
  echo 'Expected bootstrap or verify' >&2; exit 2
fi
./gradlew "${args[@]}" \
 :waltid-services:waltid-issuer-api2:buildFatJar \
 :waltid-services:waltid-wallet-api2:buildFatJar \
 :waltid-services:waltid-verifier-api2:buildFatJar
