# nusacred additions to upstream third-party notices

The original LICENSE, NOTICE.md and THIRD-PARTY-NOTICE.md are retained as upstream
history. The controlled build replaces the original COSE snapshot entry with the
source project under `third-party/cose-java`.

COSE-JAVA source: walt-id/cose-java commit
`fc897fa9da31f35c5f2e3e092496ad1c57e10457`, BSD-3-Clause. The original copyright,
conditions and disclaimer are retained verbatim in `third-party/cose-java/LICENSE`
and in the built JARs under `META-INF/licenses/cose-java/LICENSE`. Source file
headers, attribution and content are unchanged. See that module's README and
upstream-source.json for provenance and dependency changes.

The custom kotlinx.serialization 1.11.1-waltid-20260811 artifacts retain Apache-2.0
terms and JetBrains attribution, with the walt.id fork notice identifying its CBOR
tree API and behavioral changes. Source JARs were compared with commit
`4fe61aca0dd185b0cdb920a050df81dab121cae9` on `walt-id/kotlinx.serialization`.
License and attribution files are retained verbatim under
`ci/licenses/kotlinx-serialization/` and packaged under
`META-INF/licenses/waltid-kotlinx-serialization/` in each API2 fat JAR.

This addendum covers the COSE replacement and custom serialization attribution. It does not certify the completeness
of the existing upstream notice or the licenses of the entire release graph.
