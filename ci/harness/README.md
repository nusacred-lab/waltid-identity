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

Run only on an ephemeral Linux CI runner. No service ports are published to the host; a Python runner in the same internal Docker bridge uses service aliases. External DNS forwarding and routes are blocked. A new
private directory and distinct issuer/token P-256 keys are created per run by
JDK JCA. An existing runtime directory is rejected. No local runtime, user
wallet data or persistent developer volumes are mounted. Containers run without
root, extra Linux capabilities or privilege escalation, with read-only root
filesystems, private writable temporary storage and disposable wallet storage.
Issuer/verifier temporary mounts use `noexec`. Wallet requires `exec` on its
private temporary mount because SQLite JDBC extracts/loads its native library
there, as documented by [the driver](https://github.com/xerial/sqlite-jdbc/blob/master/USAGE.md).
An isolated probe using the same reviewed SQLite 3.53.2.0 JAR and pinned JRE
failed on `noexec` and connected on `exec`; this does not replace the full HTTP
flow. No capabilities, root access or writable root filesystem are added.

The actual Docker configuration, mount sources/targets, privileges and exit state are verified. Six mutations of captured inspection data must be rejected without weakening live containers. The runner receives no private key mount. Fresh-key generation and overwrite rejection produce fixed-schema evidence. See [the demo policy](../DEMO-SUPPLY-CHAIN.md) for the explicit inherited-history disposition and production prohibition.

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
