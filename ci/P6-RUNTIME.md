# P6 common JVM runtime

The API2 image recipe uses the common synthetic-demo JVM runtime built, scanned
and keylessly signed by `nusacred-lab/platform-infra`. This replaces the older
Temurin runtime affected by the October Java/CA advisories. It does not change
protocol source, Gradle dependencies, issuer/holder keys or credential state.

The runtime is pinned to
`ghcr.io/nusacred-lab/competency-proof-jvm-runtime@sha256:ecbcd98b260eac22078f57b46422999409094325a44d5f12e2f0b8ac6de90a89`.
It contains checksum-pinned Temurin 21.0.13+9 and Ubuntu CA package
20260816ubuntu0.24.04.1 (USN-8944-1). The source archive SHA-256 is
`a535a1df9c6284d9618872984e026ae0352d1f7e9e0605425c0e6114f47351dd`.

Build/scan/sign evidence:
https://github.com/nusacred-lab/platform-infra/actions/runs/39895357121
Workflow source: `62f48c4331a694687833499038ea400c20cfb77a`,
`.github/workflows/runtime-base.yml`, `refs/heads/codex/p6-release`.
Verify the image's signature, SLSA provenance and CycloneDX attestation against
that exact workflow identity/commit before accepting a replacement digest.

The infrastructure release pipeline publishes candidate service images after its
source/runtime/image gates. Fork baseline CI continues to build/test/scan local
images without registry write privileges. The G1 inherited-history exception,
expiry and isolated synthetic scope remain in force; no production eligibility
or independent review is implied by image publication.
