# Source-built COSE-JAVA

This module replaces `org.cose:cose-java:1.1.1-WALT-SNAPSHOT` with a build from
24 unchanged Java files at
[walt-id/cose-java fc897fa9da31f35c5f2e3e092496ad1c57e10457](https://github.com/walt-id/cose-java/tree/fc897fa9da31f35c5f2e3e092496ad1c57e10457).
The upstream repository is archived. Source files match both that commit and the
published timestamped source JAR; the original dirty-build binary is not consumed.

`upstream-source.json` records the original source hashes and source JAR hash.
Run `python3 ci/verify-cose-source.py` from the parent build before building.
Changes to upstream Java or LICENSE require explicit review and a manifest update.
New project tests are separate under `src/test`; no crypto implementation was rewritten.

## Identity and dependency decisions

- Local project: `:third-party:cose-java`.
- Artifact identity: `dev.nusacred.thirdparty:cose-java:1.1.1-fc897fa9-nusacred.1`.
  JAR base name is `nusacred-cose-java`. There is no publishing task or new registry.
- JDK 21, `--release 17`, preserves the baseline Java 17 bytecode target. Canonical
  CI toolchain is Temurin `21.0.12+1`.
- BouncyCastle `jdk18on` uses the parent's pinned catalog (`1.86` initially), matching
  the earlier API2 runtime lock state. LTS modules are not introduced.
- CBOR `5.0.0-alpha2` preserves the dependency/API selected by the original POM;
  this pre-release remains explicit and must still pass dependency scanning.
- SLF4J uses the parent's `slf4j-simple` version (`2.0.20` initially), already used
  for API2 compilation. The original binary introduced `2.1.0-alpha1` at runtime;
  this build uses the stable catalog API for the source's ordinary logging calls.
- Lombok `1.18.36` is compile-only plus annotation processor, matching upstream's
  source build. It is not a runtime dependency.

The parent build uses explicit project dependencies and a transitive substitution
for `org.cose:cose-java`, preventing fallback to the opaque Maven binary. The
`verifyCoseReplacement` task checks all three API2 runtime graphs for that property
and rejects duplicate BouncyCastle LTS modules.

## License and provenance

COSE-JAVA retains its original BSD-3-Clause terms; see LICENSE. The exact license
and source manifest are included in both binary and sources JARs at:

- `META-INF/licenses/cose-java/LICENSE`
- `META-INF/nusacred/cose-java/upstream-source.json`

This module is not relabeled Apache-2.0. Parent/project additions retain their own
license. Rebuilds do not copy the original `git.dirty=true` metadata or dirty POM.

## Verification

`bash ci/test-cose.sh verify` runs the isolated module with reviewed dependency
metadata. Its tests generate ephemeral keys and check seven signature algorithms,
wrong-holder/content rejection, external authenticated data, AES-GCM tampering,
MAC tampering and malformed Sign1 input. It also builds both JARs twice with task
reruns and cache reuse disabled for task outputs, comparing SHA-256 and checking
license/provenance packaging and Java 17 bytecode.

`bash ci/test-cose.sh cose-bootstrap` collects candidate dependency hashes/locks
on a temporary runner; it does not approve those hashes. The standalone settings
file deliberately uses Maven Central only. In the parent multi-project build,
the parent's global verification metadata applies instead of the standalone file.

The full baseline build also tests fresh-key mdoc issuance, issuer chains, holder
binding and tamper rejection via three existing JVMMdocTest methods, and rebuilds
all three API2 fat JARs. COSE acceptance does not by itself close G1.
