# Inherited frontend dependency remediation

These checks cover upstream documentation/examples included by the complete
source scan. The project product UI milestones continue to use the planned
Compose Web/Wasm portal and Android application.

The three npm graphs use strict peer validation. The previous
`legacy-peer-deps=true` setting was removed after fresh strict resolution passed.
Nuxt remains on the patched 3.x family. The credentials documentation migrates
Content 2 to Content 3 to replace the vulnerable MDC parser, and Image 1 to Image
2 to replace the vulnerable sharp dependency. The collection retains
`src/content`, the page renderer uses the official collection query API, and
the existing syntax theme/languages are retained with the new configuration.
Navigation, surrounding pages, table of contents and server JSON routes also
use the Content 3 APIs. The already-reviewed Minimark codec converts its stored
AST for JSON extraction instead of introducing a new Markdown parser.

Sources used for the migration:

- [Content migration](https://content.nuxt.com/docs/getting-started/migration)
- [Collection sources](https://content.nuxt.com/docs/collections/sources)
- [Highlight configuration](https://content.nuxt.com/docs/getting-started/configuration)
- [Image 2 migration](https://github.com/nuxt/image/releases/tag/v2.0.0)

Before accepting the lockfiles, all **1,270 distinct registry archives** were
downloaded separately, matched to both lock SHA-512 and official npm version
metadata, and checked for package identity. Two bundled component occurrences
are covered by their parent archive and inspected package manifests.
DefinitelyTyped archives use different root directory names; the review requires
one unambiguous root package manifest and the same registry name/version/hash.
The ledger records integrity consistency. Publisher build attestations and
registry signatures have not been verified.

`verify-npm-review.py` rejects changed manifests, unreviewed archives and changed
bundled versions. Its negative checks were exercised on private copies, including
an unknown archive whose lock-file checksum was deliberately updated: the
missing per-archive review still caused rejection.

CI uses the official Node 22.23.1 Debian builder at the exact linux/amd64 manifest
in `frontend-toolchain.json`. The npm 11.21.1 archive and Node native headers have
separately checked hashes in `tools.json`. npm 10 encountered an internal Arborist
error during resolution; npm 11 completed all three graphs with strict peer
checking. Resolver failure was never treated as acceptance.

The networked container installs packages with all lifecycle scripts disabled.
Rebuild, native compilation, application build and documentation HTTP tests then
run in a separate container with **no network**. Verified Node headers are
provided locally and source builds are requested for native lifecycle compilation.
Platform binaries already included in reviewed npm archives retain those archive
hash guarantees. No additional binary download is allowed to succeed during
package scripts. Containers run without root, extra
capabilities or privilege escalation; only disposable source copies and reviewed
tool directories are mounted. Raw package/build logs are withheld. Evidence
contains fixed-schema outcomes and failure categories.

Documentation regression checks require real SSR output for the root and a
nested mdoc page, including headings, navigation, surrounding links and TOC,
plus HTTP 404 for a missing page. Three credential JSON APIs must list and
return data matching the original Markdown fixtures and reject unknown names.
Mapping/manifest extraction uses a versioned synthetic Markdown fixture overlaid
only in the disposable test copy; evidence identifies that overlay. The actual
HTTP handlers and parser run against it. The other two upstream apps must
compile. These jobs must pass before the frontend changes are accepted.

As of 2026-10-20, local source scanning including development dependencies still
reports `CVE-2026-85393` in `node-forge` 1.4.0 and `CVE-2026-93687` in `braces`
3.0.3 in both Nuxt graphs. These remain the latest official registry releases
observed during review. No waiver or ignore is added. Full-history findings
also remain open; **G1 stays blocked** until the remaining security work passes.
