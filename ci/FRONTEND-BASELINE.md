# Retained frontend and catalog scope

On 2026-10-21 the unused Nuxt demo portal (`waltid-web-portal2`) and the
Nuxt runtime of `waltid-credentials` were retired from this fork. The Nusacred
product clients are the planned Compose Web/Wasm portal and Android APK.
Neither retired frontend is required by the three API2 services or the real
HTTP credential acceptance harness. This removes unsupported examples and their
deployment targets; it does not claim that their vulnerabilities were patched.

The dependency-parent review found official current listhen 1.10.1 still requires
node-forge ^1.4.0; micromatch 4.0.8 and fast-glob 3.3.3 still lead to braces ^3.0.3.
Content 3.16.2 also requires micromatch, so upgrading Nuxt alone cannot remove all
paths. Official npm latest versions observed on 2026-10-21 remain node-forge
1.4.0 and braces 3.0.3. No local crypto patch, package identity rewrite, CVE waiver
or scanner directory exclusion is used.

Compatibility changes:

- The Nuxt interactive demo portal is no longer supplied or deployable.
- The credential catalog is source-only. All 56 Markdown/navigation/asset files
  under its src/content and src/public retain their exact bytes and paths.
  credential-catalog-source.json and verify-catalog-scope.py compare their complete
  inventory and bytes against immutable pre-retirement commit
  51daa3381dfb434265572c33c8f0ac5fd3687df0.
- Catalog SSR and its list/credential JSON/mapping/manifest routes no longer
  exist. Historical endpoint descriptions in preserved documentation are
  references, not a promise of local service. API2 credential definitions are
  embedded in service configuration; acceptance must prove issuance/verification
  without either frontend.
- Inherited example Compose services web-portal2 and vc-repo, their proxy listeners
  and published ports are removed. Imported deployment workflows stay quarantined;
  their historical references do not deploy here.
- No product APK or Compose portal is claimed implemented by this removal.

The previous Nuxt security migration built and tested successfully before
retirement (baseline 39469433273 and checks 39469433322), but left four High
findings in the two unused graphs. Previous source and archive review evidence
remain in Git history; complete-history secret scanning is not shortened.

The remaining waltid-digital-credentials example retains its existing lock graph,
with 65 distinct npm archives already reviewed by separate downloads, registry
metadata/SHA-512 and package identity checks. The ledger is exactly the subset
used by this graph; no new hashes are accepted. Bundled components remain bound
to their reviewed parent archive. This establishes integrity consistency, not
publisher build attestation or source audit.

CI retains strict peers, pinned Node 22.23.1/npm 11.21.1/header hashes and an exact
official builder image. Installation disables lifecycle scripts; rebuild/build
execute without network, root, extra capabilities or a writable root filesystem.
The retained example must build. Removed application tests retire with their
implementations; a source-preservation/scope check guards the documented change.
Source SCA still scans the entire current tree including development dependencies.

Full-history secret findings remain an independent blocker. Application removal
does not resolve historical credentials or establish that G1 has passed.
