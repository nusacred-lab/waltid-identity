# G1 protocol harness

This is an isolated adaptation of the project's existing real HTTP harness.
It uses the same competency profile and SD-JWT issuance/presentation payloads;
it does not simulate issuer, wallet, verifier or cryptography. The source is
project-authored under Apache-2.0; upstream notices remain applicable to services.

`ci/test-baseline-images.sh` builds only the three previously hashed fat JARs,
using the pinned official Temurin 21 JRE / Ubuntu 24.04 linux/amd64 manifest.
The initial base-image scan on 2026-10-20 found zero High/Critical vulnerabilities
with Trivy 0.76.0; every run scans the actual assembled images again. Each image
must pass before the protocol test starts. No registry credentials or publish
permissions are used. `images-tested.json` records source, fat-JAR SHA-256, base
manifest digest and local image **configuration** digest. The latter is not
claimed to be a published registry manifest digest.

Run only on an ephemeral Linux CI runner with unused ports 7004–7006. A new
private directory and distinct issuer/token P-256 keys are created per run by
JDK JCA. An existing runtime directory is rejected. No local runtime, user
wallet data or persistent developer volumes are mounted. Containers run without
root, extra Linux capabilities or privilege escalation, with read-only root
filesystems, private writable temporary storage and disposable wallet storage.

The positive protocol flow creates a wallet and holder key, receives/stores a
credential from the real issuer, previews the real presentation request, sends
a holder-bound presentation and requires `SUCCESSFUL` from the real verifier.
COSE/mdoc tamper and wrong-holder tests are separate prerequisites. This does
not replace later application authorization, Keycloak, APK or recovery gates.

Only fixed-schema outcomes, SBOMs, vulnerability reports and build identities
are uploaded. Keys, runtime configurations, access-bearing protocol responses
and container logs are withheld. Failures stop the job and name the failed
protocol stage without printing response bodies. Cleanup removes only the
resources created by that invocation, including its temporary wallet data.
