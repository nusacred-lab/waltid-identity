---
title: G1 Contract Fixture
navigation: false
---

# G1 Contract Fixture

Synthetic documentation input used only in the isolated build test.

```json
{
  "type": ["VerifiableCredential", "G1Contract"],
  "credentialSubject": { "id": "urn:g1:synthetic-subject" }
}
```

## Mapping

```json
{
  "id": "<uuid>",
  "issuer": { "id": "<issuerDid>" }
}
```

## Manifest

```json
{
  "id": "g1-contract",
  "output_descriptors": [{ "id": "g1-output", "schema": [{ "uri": "urn:g1:contract" }] }]
}
```
