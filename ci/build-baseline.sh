#!/usr/bin/env bash
set -euo pipefail
mode="${1:-verify}"
args=(--no-daemon --no-configuration-cache --max-workers=2 -Dorg.gradle.jvmargs=-Xmx6g -I ci/locking.init.gradle)
if [[ "$mode" == bootstrap ]]; then
  args+=(-Pp1Bootstrap=true --write-locks --write-verification-metadata sha256)
elif [[ "$mode" == verify ]]; then
  if [[ ! -s gradle/verification-metadata.xml || ! -s build-logic/gradle.lockfile ]]; then
    echo 'Reviewed verification metadata and build-logic lock are required; bootstrap output must be reviewed first.' >&2
    exit 1
  fi
  python3 ci/verify-dependency-review.py
  args+=(--dependency-verification strict)
else
  echo 'Expected bootstrap or verify' >&2; exit 2
fi
python3 ci/verify-cose-source.py
./gradlew "${args[@]}" \
 :third-party:cose-java:check \
 verifyCoseReplacement \
 :waltid-services:waltid-issuer-api2:buildFatJar \
 :waltid-services:waltid-wallet-api2:buildFatJar \
 :waltid-services:waltid-verifier-api2:buildFatJar \
 collectBaselineRuntimeEvidence

# These existing integration tests generate fresh issuer/device keys and exercise
# mdoc signing, issuer chains, presentation holder binding and tamper rejection.
./gradlew "${args[@]}" :waltid-libraries:credentials:waltid-mdoc-credentials:jvmTest \
 --tests id.walt.mdoc.JVMMdocTest.testSigningMdlWithIssuer \
 --tests id.walt.mdoc.JVMMdocTest.testSigningMdlWithIntermediateIssuer \
 --tests id.walt.mdoc.JVMMdocTest.testSigningMdlWithOnlyTheIntermediateIssuerCertInX5Chain
python3 ci/check-baseline-tests.py
