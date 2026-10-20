# Initial P1 Security Assessment

Initial date: 20 October 2026. Current G1 status follows the required checks and
[isolated demo policy](../../ci/DEMO-SUPPLY-CHAIN.md); earlier sections record
historical results. Upstream baseline: v1.2.0,
`ef516ecec4c79fd9fba6f1e8b226b52a4e8cf790`. No blanket exceptions, global
allowlists, history deletion, or production image promotion are permitted.

## Scope and results

- Gitleaks 8.30.1 over the complete upstream Git history: 2,282 findings across
  388 paths. Review was incomplete; fixture status requires confirmation for
  each finding before an exception. This count does not establish how many
  active credentials were exposed.
- All 10 new blobs in bootstrap `d7342909117e44a99ed4f9ecfa324eccc2b08083`
  were checked separately: zero findings. Other blobs were identical to the
  public upstream baseline. This allowed publication of changes without secrets;
  it did not pass the baseline scan.
- Trivy 0.76.0 source SCA: eight targets, 11 High and zero Critical findings in
  detected manifests. The findings below concern two upstream frontend
  applications, outside the issuer2/wallet2/verifier2 target images. They remain
  recorded and are not ignored.
- Source CycloneDX SBOM: 239 components. **Resolved Gradle/JAR dependencies and
  candidate-image OS packages were not covered.** This count does not establish
  JVM coverage.
- Full reports that might contain tokens or keys remain private. This document
  contains only summaries and public package metadata.

## Source SCA findings

| Target | Package | Version | Finding | Severity | Fix reported by scanner database |
| --- | --- | --- | --- | --- | --- |
| `waltid-applications/waltid-credentials/package-lock.json` | `node-forge` | 1.4.0 | CVE-2026-85393 | HIGH | Unavailable in scan results |
| `waltid-applications/waltid-credentials/package-lock.json` | `sharp` | 0.32.6 | GHSA-f88m-g3jw-g9cj | HIGH | 0.35.0 |
| `waltid-applications/waltid-credentials/package-lock.json` | `sharp` | 0.32.6 | GHSA-rgj7-g3m4-5g8c | HIGH | 0.35.4 |
| `waltid-applications/waltid-credentials/package-lock.json` | `sharp` | 0.32.6 | GHSA-wq5f-xc86-pv6w | HIGH | 0.35.5 |
| `waltid-applications/waltid-credentials/package-lock.json` | `source-map-js` | 1.2.1 | CVE-2026-93749 | HIGH | 1.2.2 |
| `waltid-applications/waltid-credentials/package-lock.json` | `svgo` | 3.3.4 | CVE-2026-84370 | HIGH | 2.8.4, 3.3.5, 4.1.0 |
| `waltid-applications/waltid-web-portal2/package-lock.json` | `@vue/server-renderer` | 3.5.38 | GHSA-g2v6-rqmx-r4w6 | HIGH | 3.5.42, 3.6.0-rc.6 |
| `waltid-applications/waltid-web-portal2/package-lock.json` | `nanoid` | 3.3.12 | CVE-2026-67213 | HIGH | 3.3.18, 5.1.6 |
| `waltid-applications/waltid-web-portal2/package-lock.json` | `nanoid` | 3.3.12 | CVE-2026-67214 | HIGH | 3.3.16, 5.1.16 |
| `waltid-applications/waltid-web-portal2/package-lock.json` | `postcss` | 8.5.15 | CVE-2026-73646 | HIGH | 8.5.18 |
| `waltid-applications/waltid-web-portal2/package-lock.json` | `source-map-js` | 1.2.1 | CVE-2026-93749 | HIGH | 1.2.2 |

## Custom artifacts and build integrity

| Coordinates | Baseline version | Remaining checks at this stage |
| --- | --- | --- |
| `org.cose:cose-java` | `1.1.1-WALT-SNAPSHOT` | Replaced by pinned source project `:third-party:cose-java`; see remediation below. The snapshot binary is not accepted as trusted. |
| `id.walt:waltid-nftkit` | `1.2311291144.0` | Alias for web3login; establish whether it enters target dependencies. Catalog presence does not prove inclusion in the three API2 services. |

COSE investigation on 20 October 2026 identified timestamped snapshot
`1.1.1-WALT-20250317.122639-2`, published at
`https://maven.waltid.dev/snapshots/org/cose/cose-java/1.1.1-WALT-SNAPSHOT/`.
The binary contains `git.properties` with commit
`fc897fa9da31f35c5f2e3e092496ad1c57e10457` and **`git.dirty=true`**.
All 24 Java files in the source JAR matched that source commit in
[walt-id/cose-java](https://github.com/walt-id/cose-java/tree/fc897fa9da31f35c5f2e3e092496ad1c57e10457)
after line-ending normalization, with no missing paths. That repository is now
archived.

The published POM differs from the claimed commit's POM: BouncyCastle
`bcprov-jdk18on`/`bcpkix-jdk18on` 1.80 was replaced by
`bcprov-lts8on`/`bcpkix-lts8on` 2.73.7. Neither binary nor source JAR contains
LICENSE/NOTICE; the source commit contains LICENSE. Source agreement does not
prove that the binary was built exclusively from that source. POM provenance,
LTS dependencies, binary/source verification, and license packaging still
required resolution at this stage.

Downloaded SHA-256 values from the investigation (not yet accepted release
verification metadata):

| Timestamped snapshot artifact | SHA-256 |
| --- | --- |
| Binary JAR | `f69dbdabcf8ead0b78d6d36098538f0febbfa38b07114b1965816741b671419e` |
| Source JAR | `8fc17a7c02b21a2d5326853986840ad098dfc51a53b21a5f1468c001685142a3` |
| POM | `3638b3a4df74a42dc455204a657c7b96af759650cabfc49009bf5fa5e8de2654` |

A direct `identityLibs.java.cose` reference was found in mdoc-credentials, used
by issuer2; the actual target dependencies therefore required inspection.
`id.walt:waltid-nftkit` was found in web3login-microservice, which does not prove
inclusion in the three API2 classpaths. Resolved build results are authoritative.

Declared repositories: Maven Central, Google, Gradle Plugin Portal,
`https://maven.waltid.dev/releases`, and `https://maven.waltid.dev/snapshots`.
At this stage no lock/verification metadata had been accepted for target or
build-logic dependencies. The [isolated bootstrap](https://github.com/nusacred-lab/waltid-identity/actions/runs/39398624224)
at `81268c0739156071a2c61626a247ed4ae748fc4a` built all three API2 fat JARs in
15 minutes 1 second. It did not build or test images. Artifact `12253803181`
contained 156 lockfiles and verification metadata with 1,866 components and
3,402 SHA-256 entries, all still unaccepted candidates.

Review found the COSE snapshot in all three API2 lockfiles and 33 lockfiles in
total, but no `org.cose` component in verification metadata. This matches the
[Gradle dependency verification limitation](https://docs.gradle.org/current/userguide/dependency_verification.html)
for changing/SNAPSHOT dependencies. Gradle 9.8.0 also warned that snapshot locking
does not freeze artifact contents. Strict mode cannot be claimed to protect that
artifact simply because other checksum metadata is present.

`ci/build-baseline.sh bootstrap` only collects candidate metadata; `verify`
rejects missing metadata and uses strict verification. Never run write-metadata
on the release path to accept new checksums.

The wrapper JAR matched its official checksum:
`238e777fcddd7e34f9708186085def2abd6e08e658505b38718d79d74c21abd5`.
The Gradle 9.8.0 distribution uses SHA-256:
`bafd5ce9cfaea0fbccfdc8439a1ac42fbd4cd9c89dc9a988228d8a2639a58e6c`.
Checksum sources: https://services.gradle.org/distributions/gradle-9.8.0-wrapper.jar.sha256
and https://services.gradle.org/distributions/gradle-9.8.0-bin.zip.sha256.

Upstream LICENSE, NOTICE.md, and THIRD-PARTY-NOTICE.md are retained. The notice
lists 867 components and license texts under `LICENSES/`, but that directory is
absent from this source baseline. Target license auditing and packaged texts
still required checking before image distribution. Static notices do not
establish review of every release dependency.

## Building COSE from source

Remediation replaced all direct COSE declarations (nine usages in eight build
files) with `:third-party:cose-java`, and added transitive substitution to prevent
fallback to the external `org.cose:cose-java` binary. Local identity:
`dev.nusacred.thirdparty:cose-java:1.1.1-fc897fa9-nusacred.1`. All 24 Java files
and LICENSE match the pinned source manifest byte for byte; upstream cryptographic
implementation was not rewritten. BSD-3-Clause LICENSE and provenance are
packaged in binary and source JARs. Additional notices retain attribution.

The module uses BC `jdk18on` 1.86, consistent with prior API2 resolution, without
LTS. CBOR 5.0.0-alpha2 is retained explicitly. Lombok 1.18.36 is compile/annotation
processing only; SLF4J API uses catalog version 2.0.20. See
[module decisions and limitations](../../third-party/cose-java/README.md).

[COSE discovery](https://github.com/nusacred-lab/waltid-identity/actions/runs/39439984065)
passed 13 tests without skips and produced identical binary/source JARs across
two rebuilds with task caching disabled. [Strict PR CI](https://github.com/nusacred-lab/waltid-identity/actions/runs/39441236360/job/118691321626)
then passed `cose-acceptance`, using strict dependency verification and locking
without writing new checksums. The overall run still failed the baseline gate
because global metadata had not been accepted. The COSE job alone did not pass G1.

Standalone review matched 38 hashes from 20 components against separate Maven
Central downloads. The lock contains 18 coordinates including test dependencies.
Trivy 0.76.0 recognized 17 dependency JARs and 18 lock coordinates, including dev,
with no findings; database update: 20 October 2026 07:17:35 UTC. This is neither a
cryptographic code audit nor a full runtime/image scan. The focused dependency
SBOM contains 17 components.

Tests exposed an upstream limitation: the Ed25519 generator populates the COSE
map but does not initialize its cached JCA key. Tests import a serialized COSE key
through the validating/initializing constructor, then test signatures and
rejection of another key or tampered content. The direct generator bug is not
claimed to be fixed.

[COSE source integration](https://github.com/nusacred-lab/waltid-identity/actions/runs/39440113754)
at `78cb982f0181c997721846666c2331725d35dbaf` succeeded in 15 minutes 43 seconds.
All three API2 fat JARs built; `verifyCoseReplacement` passed issuer/wallet/verifier
graph checks without external COSE binaries or BC LTS. Three fresh-key
JVMMdocTest scenarios passed: issuer, intermediate issuer, and intermediate issuer
in x5chain. These cover issuance, tampered-content rejection, and device-signed
presentation. They do not test HTTP or the image credential harness. Global
bootstrap metadata remained candidate material; bootstrap success does not replace
the strict gate. Subsequent changes only affected standalone metadata/settings,
CI gates, manifest checking, and documentation; production source and parent-build
dependencies remained the same.

The baseline gate depends on COSE test/repeatability results. A COSE job failure
must explicitly fail the required baseline check rather than leave it skipped.
Workflows remain read-only, without registry, signing, or deployment privileges.
Standalone metadata applies only to the isolated module build; the parent build
requires separate review of all its metadata/plugins. Initial findings above
remained open at this stage.

## Global review and actual runtime — G1 continuation

[Discovery 39449623992](https://github.com/nusacred-lab/waltid-identity/actions/runs/39449623992)
at `784162061f2b4a42c48c1423cf303afb93f0ea45` passed three API2 builds, the COSE
graph guard, mdoc tests, fat JAR attribution, and actual-runtime scans through
both resolved graphs and direct JAR inspection. Both reported **zero
High/Critical** for issuer, wallet, and verifier. Graph SBOMs contain 340, 405,
and 306 artifacts respectively, matched against each JAR's SHA-256. The SBOM does
not claim every transitive dependency edge; its root list covers all runtime
artifacts. This did not yet establish image scans or image HTTP flows.

Global metadata with **1,872 components/3,431 hashes** and **159 lockfiles** was
accepted after separate review. Of the initial 3,398 candidate hashes, 1,626
matched official repository checksums, 1,336 matched independently hashed official
downloads, 383 matched official `.module` mappings followed by download hashing,
52 matched custom publisher artifacts, and one Kotlin/Native archive matched the
official JetBrains release asset digest. Another 65 hashes were checked after
dependency remediation; some replaced earlier versions, so the final count is not
3,398 + 65.

Custom serialization `1.11.1-waltid-20260811` was traced to
[source fork `4fe61aca0dd185b0cdb920a050df81dab121cae9`](https://github.com/walt-id/kotlinx.serialization/tree/4fe61aca0dd185b0cdb920a050df81dab121cae9).
All 946 source-JAR code-file comparisons across targets matched after line-ending
normalization (common source repeats; these are not 946 unique files). License
and fork notices are retained exactly in `ci/licenses/kotlinx-serialization`
and checked in fat JARs. Neither attestation nor binary reproduction was found;
neither is claimed. Fork-specific CBOR behavior is retained. The snapshot
repository was removed. The walt.id release repository is limited to that
serialization version and specific legacy NFTKit coordinates, rather than acting
as a general mirror.

Runtime remediation uses Netty 4.1.138 for issuer and 4.2.18 for wallet/verifier,
Jackson 2.22.3/3.2.3, json-smart 2.5.2, and PG JDBC 42.7.14. BC tooling 1.86 and
jose4j 0.9.6 are also pinned. Every hash requires an exact review entry in
`ci/dependency-review.json`; unreviewed XML, lock-content, or lock-inventory changes
are rejected. Acceptance runs Gradle strict without write-metadata or automatic
promotion from bootstrap.

[Earlier discovery 39445432407](https://github.com/nusacred-lab/waltid-identity/actions/runs/39445432407)
remains **failed**: the collector read the `buildFatJar` lifecycle output
incorrectly. It now reads the `shadowJar` archive. Partial candidates lacking the
full lock inventory from that failed run were not imported. Negative tests reject
changed metadata/locks, new unreviewed locks, changed runtime JARs, and fat JARs
without attribution.

[Strict acceptance 39451595960](https://github.com/nusacred-lab/waltid-identity/actions/runs/39451595960)
**failed** at wallet readiness: SQLite JDBC could not initialize its native
library on a `noexec` temporary mount. An isolated probe with the same SQLite
3.53.2.0 JAR and pinned base JRE failed with `noexec` and passed with `exec`.
The fix limits executable temporary mounts to the wallet; other containers retain
`noexec`, root filesystems remain read-only, and processes remain non-root.

[Strict acceptance 39454853516](https://github.com/nusacred-lab/waltid-identity/actions/runs/39454853516)
at head `60d8c522aff10ae87537a29243ddc403ce2047b3` **passed**: 13 COSE tests,
three mdoc tests, no failures/errors/skips, zero High/Critical runtime/image
findings for all three services, and real HTTP issuance, wallet storage, preview,
holder-bound presentation, and verification. No images were published.
[Source/digest evidence](evidence/g1-api2-39454853516.json) records the actual
built merge commit and its tree equality with the PR head. Local image
configuration digests are distinguished from registry manifest digests.

## Complete source and further remediation — 20–21 October 2026

Initial scans omitted some frontend development dependencies. Source scans/SBOMs
now require `--include-dev-deps`. Full initial-lock coverage reported **213
High/15 Critical**; these counts do not describe findings packaged in the three
actual API2 runtimes.

Init-build patch rules remediate vulnerable compile/plugin classpaths while
retaining Jackson/Netty minor families and avoiding downgrades. API2 service BOMs
remain independent. Discovery only updates targeted lock families; strict runs
use neither update-locks nor write-metadata.
[Discovery 39459390656](https://github.com/nusacred-lab/waltid-identity/actions/runs/39459390656)
passed, including images and credential flow. **35 additional hashes** were
reviewed separately; accepted metadata contains **1,894 components/3,466 hashes
and 159 lockfiles**. Scanning all candidate Gradle locks, including dev, reported
zero High/Critical.

All three frontend graphs were updated with strict peer validation; 1,270 npm
archives were reviewed against registry metadata and separately downloaded bytes.
Bundled components and DefinitelyTyped archive-root differences were also checked.
Npm 10 encountered an internal error; integrity-checked npm 11.21.1 resolved
strictly without legacy-peer-deps. Builder Node, native headers, and npm are
pinned. Lifecycle/build scripts run offline after script-free archive installation.
See [details and scope limits](../../ci/FRONTEND-BASELINE.md).

The initial Content migration omitted some navigation/API behavior and failed SSR
tests in [run 39460484815](https://github.com/nusacred-lab/waltid-identity/actions/runs/39460484815).
Remediation added navigation, surrounding pages, TOC, and JSON endpoints using the
reviewed official AST codec. Isolated local HTTP tests on actual builds then
passed root/nested pages, TOC targets, navigation, missing-page 404s, three
credential APIs matching source Markdown and rejecting unknown names, and
mapping/manifest APIs against versioned synthetic fixtures. Final-revision CI
must rerun frontend builds and API2 acceptance before changes are accepted.

Full source scans after reviewed locks reported **4 High, 0 Critical**:
`node-forge` 1.4.0 / CVE-2026-85393 and `braces` 3.0.3 / CVE-2026-93687 across
two frontends. Official registries had no fixes when checked. GitHub dependency
review also rejected braces. No waiver, ignore, or package namespace change was
used to hide findings from scanners.

Upstream history still contained 2,282 findings, privately grouped into 361
distinct values for triage. Grouping does not establish false positives or active
credentials. Three AWS/Azure groups lacked fixture/revocation confirmation. No
authentication attempts or public reports used these values. **G1 remained blocked
at this stage.**

### One checksum finding established as non-secret

A subsequent revision added one generic-api-key finding in the checksum of a test
result file whose name contains credential, raising the raw count to 2,283.
The value exactly matches the SHA-256 of a
[safe public outcome file](evidence/g1-api2-39454853516-outcome.json): schema
version, booleans, and passed status only, without credentials, keys, grants, or
session IDs. Commit/line locations and proof are recorded in the
[classification ledger](../../ci/checksum-finding-review.json).

Only that immutable fingerprint enters `.gitleaksignore`.
`ci/verify-checksum-findings.py` checks the original-commit source, finding line,
proof byte hash, and outcome schema on every CI run. Additional ignores without
proof and changed proofs are rejected. Both negative tests were performed;
fingerprint-set comparison confirms only that checksum finding was removed and
**the other 2,282 findings still blocked full-history scanning**. This introduces
neither a CVE exception nor a directory/baseline-history allowlist.

## Subsequent gates

1. Retain COSE source, review ledgers, and compatibility results. New dependencies
   or hashes require review, including lock-inventory changes.
2. Demonstrate the strict path without metadata changes or skipped tests.
3. Pass image scans and real credential flows on the same images. Record
   source/JAR/base digests and local image configuration digests with the correct
   digest types. These workflows do not publish to registries.
4. Address source/frontend and inherited-history findings individually. Required
   security checks must block either failure. Blanket exceptions are prohibited.

Scanner errors, incomplete metadata, and unresolved findings block G1, subject to
the later explicitly bounded demo decision below.

## Scope remediation — 21 October 2026

The two unused Nuxt runtimes and their deployment targets have been retired;
credential Markdown/navigation/assets remain byte-exact source references. The
API2 runtime and planned Compose/Android product clients do not depend on them.
See [scope, compatibility losses and preservation checks](../../ci/FRONTEND-BASELINE.md).
This removes vulnerable dependency graphs rather than claiming upstream CVEs
fixed or adding CVE exceptions. The retained example uses 65 already-reviewed
npm archives. The complete current-tree source scan, including development
packages, reports zero High/Critical locally; final CI and real API2 image
acceptance must still confirm the revised commit.

Full Git history is unchanged. Prioritized private triage found unconfirmed AWS
credential material and an Azure client secret previously used by code making
real token requests. Neither revocation nor fixture status is established. No
provider authentication is attempted; values remain private. History checks
must remain blocked pending evidence. No exception or mass allowlist is granted.

## Demo scope decision — 21 October 2026

The maintainer explicitly requested a demo-oriented supply-chain demonstration
without external reporting. Known inherited history is now handled by the
expiring exact-inventory policy G1-DEMO-HISTORY-20261021, not by asserting fixture
status or revocation. All 2,282 findings remain visible; new findings, changed
coverage, altered inventory, scanner failure and production scope are rejected.
Only an internal, disposable runtime with fresh keys may use this disposition.
Source/runtime/image vulnerability gates and strict dependency review remain
mandatory. Read-only workflows cannot publish, sign or deploy.

See [policy and containment](../../ci/DEMO-SUPPLY-CHAIN.md) and the sanitized
CI source-control/runtime artifacts for actual outcomes. No external report
was sent and no upstream confirmation is required for this bounded demo policy.
Historical claims of blocked G1 above are superseded only when all current
required checks and the new containment checks pass on the same head.
