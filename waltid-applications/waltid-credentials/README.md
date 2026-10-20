# Credential catalog source

This fork retains the Markdown credential examples in `src/content` and their
assets in `src/public` as reference material. Their bytes are checked against
`ci/credential-catalog-source.json`, sourced from commit
`51daa3381dfb434265572c33c8f0ac5fd3687df0`.

The inherited Nuxt website, hosted credential JSON/mapping/manifest API and its
npm dependency graph have been retired. This directory is not a runnable app
or deployment target. Existing example endpoint descriptions are historical;
no local service implements them. The upstream source remains in Git history.

The product uses issuer/wallet/verifier API2, a Compose Web/Wasm portal and an
Android APK. API2 configuration embeds its credential definitions and does not
load the retired catalog server during the acceptance harness. The previous
Nuxt site and demo portal are not a replacement for those product clients.
