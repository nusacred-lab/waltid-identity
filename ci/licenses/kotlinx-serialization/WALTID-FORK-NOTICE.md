# walt.id fork notice

This repository is a walt.id fork of [Kotlin/kotlinx.serialization](https://github.com/Kotlin/kotlinx.serialization).

It exists to ship the **CBOR `CborElement` tree API** ([#3036](https://github.com/Kotlin/kotlinx.serialization/pull/3036)) together with a
small number of walt.id-specific behaviour choices. 

Working branch: **`cbor-element-dev`**.

> This file is walt.id-specific documentation. It is *not* an Apache `NOTICE` file; see `LICENSE.txt` and
> `license/` for licensing and attribution.

---

## Consuming this fork

Artifacts are published to the walt.id snapshot repository:

```
https://maven.waltid.dev/snapshots
```

Group and artifact names are unchanged from upstream (`org.jetbrains.kotlinx:kotlinx-serialization-*`); only the
version is walt.id-specific:

```
1.11.1-waltid_<yyyyMMdd>-SNAPSHOT
```

---

## Merge history with upstream

### `d2d1cf25` - merge `origin/dev` into `cbor-element-dev` (2026-08-10)

Parents: `0edc1c12` (fork) + `bed6c0a2` (upstream `dev`). Brought in 16 upstream commits:

| Commit                                                 | Subject                                                                                      |
|--------------------------------------------------------|----------------------------------------------------------------------------------------------|
| `bed6c0a2`                                             | IR inliner: Don't use CLI flag that enforces "intra-module" inliner mode (#3234)             |
| `1497ac0b`                                             | Update Kotlin to 2.4 (#3230)                                                                 |
| `c4d81ac1` `38f8c450` `47d29974` `55c893e8` `63805dd6` | Semantic rename of internal entities                                                         |
| `355e9b2b`                                             | KT-87873: suppress warning on android native target family (#3229)                           |
| `f279fea0`                                             | Improve JSON decoding performance for Okio and kotlinx-io for ASCII (#3225)                  |
| `e03b33df`                                             | **CBOR: Encode unsigned integer types as positive integers (#3194)**                         |
| `d3c510d9`                                             | Prepare tests for fix for KT-75702 / #2409 (#3219)                                           |
| `84ff6afe`                                             | **CBOR: Correctly decode CborLabel values (#3195)**                                          |
| `8603551d`                                             | Stabilize various default serializers, helpers, and features (#3216)                         |
| `8d4ed616`                                             | Fix Polymorphic Deserialization Error with Subclass using JsonTransformingSerializer (#3139) |
| `e3eca227`                                             | Replaced publishing-check-conventions with the artifacts-validator-plugin (#3210)            |
| `d8d0fc8f`                                             | CBOR: include actual tag info into CborDecodingException (#3197)                             |

Conflicts were in three files; resolutions recorded below.

---

## Negative CBOR label (read this before moving branches)

Symptom: Every COSE key failed to decode. `CoseRsaKey` reported
`Expected an unsigned or negative integer, but found 43`; `CoseSymmetricKey` reported
`Field 'k' is required ... but it was missing`.

Cause: `StreamingCborParser.nextTaggedStringOrNumber()` read map keys / `@CborLabel` values with
`readUnsignedIntegerIgnoringMajorType()`, which ignores the CBOR major type. A negative integer key such as
`-1` (`0x20`) therefore decoded as the raw additional-info value `0`, `-2` (`0x21`) as `1`, and so on. COSE uses
negative labels heavily, so `@CborLabel(-2)` collided with `@CborLabel(1)`:

```kotlin
@CborLabel(1)  val kty: Int          // 1
@CborLabel(-1) @ByteString val n: ByteArray   // read as 0
@CborLabel(-2) @ByteString val e: ByteArray   // read as 1  -> matched kty, decoded a byte string as Int
```

---

## Deviations from upstream `dev`

(Preserve these across future merges)

### 5.1 Unsigned integer *encoding*: keep the fork's `UnsignedInlineEncoder`

Both branches independently implemented "encode Kotlin unsigned types as CBOR unsigned integers":

* fork - `internal/Unsigned.kt`, `UnsignedInlineEncoder` returned from `encodeInline()`
* upstream #3194 (`e03b33df`) - an `encodeNumberAsUnsigned` flag consulted in
  `encodeByte`/`encodeShort`/`encodeInt`/`encodeLong`, plus `SerialDescriptor.isUnsignedNumber`

Keeping both produced `[CONFLICTING_OVERLOADS]` on two `encodeInline` declarations. **The fork's version is
kept** because it routes through the `CborWriter` interface and therefore also covers the `CborElement` tree
writer, which upstream's flag does not. Upstream's mechanism was removed:

* `encodeNumberAsUnsigned` - removed from `internal/Encoder.kt`
* `isUnsignedNumber` / `unsignedNumberDescriptors` - removed from `internal/Encoding.kt`

Both emit identical canonical unsigned integers, so this is an implementation choice, not a behaviour change.

### 5.2 Unsigned integer *decoding*: stricter than upstream

| Input  | Meaning                  | Upstream `dev` | This fork  |
|--------|--------------------------|----------------|------------|
| `18c8` | canonical unsigned `200` | `200u`         | `200u`     |
| `3837` | legacy signed `-56`      | `200u`         | **throws** |

Older kotlinx.serialization encoded `UByte(200u)` by delegating to `encodeByte(200.toByte())`, i.e. as the
negative integer `-56`. Upstream #3194 keeps reading those legacy encodings; this fork rejects them via
`UnsignedInlineDecoder` in `internal/Unsigned.kt`.

Rationale: rejecting is what `1.11.1-waltid_20260519-SNAPSHOT` already shipped, so staying strict avoids a
behaviour change for existing walt.id consumers, and malformed unsigned data fails loudly instead of silently
round-tripping. Asserted by `CborUnsignedInteroperabilityTest.testLegacySignedEncodingsAreRejectedForUnsignedTypes`.

Consequence: two upstream tests are intentionally absent from
`commonTest/.../CborNumberEncodingTest.kt`, since they assert the opposite of the above:

* `testDecodingLegacySignedEncodingOfUnsignedValues`
* `testUnsignedArrayMixedDecoding`

A comment in that file records why. A future merge will try to reintroduce them; drop them again, or flip the
decision deliberately and delete the fork test instead. Do not "fix" one side without the other - they cannot
both pass.

### 5.3 `CborDecoderTest.testEncodeUnsignedValuesFromPositiveInteger`

Expected messages use the strict single-range form, e.g.

```
Decoded number 32000 is not within the range for type UByte ([0..255])
```

rather than upstream's relaxed combined-range form from #3167
(`... for type Byte ([-128..127]), nor it is within the range for UByte ([0..255])`).

Note: this test had been **failing on `cbor-element-dev` since unsigned decoding became strict** (`4ccf30b1`) and
was fixed as part of `d2d1cf25`. It was red before the merge, not because of it - verified by running the suite
in a detached worktree at `0edc1c12`.

### 5.4 `internal/Encoding.kt` - mixed resolution

* adopted from upstream: the `HEADER_SIMPLE` → `HEADER_FP_AND_SIMPLE` rename, and
  `majorTypeName` / `simpleValueKindName` (the sole reference in `CborTreeReader.kt` was updated)
* kept from the fork: `isCborElementDescriptor()`, `cborElementSerialNames`,
  `throwIfCborElementHasIncompatibleAnnotations()`

---

## 6. Verifying a merge

```bash
./gradlew :kotlinx-serialization-cbor:jvmTest     # 239 tests, all green at d2d1cf25
./gradlew jvmTest apiCheck                        # full JVM suite + binary-compatibility validator
```

Then publish a new dated snapshot and run the consumer build:

```bash
# in waltid-unified-build, after bumping both version catalogues
./gradlew --rerun-tasks --no-build-cache clean cleanAllTests test allTests
```

Pay attention to `waltid-cose`, `waltid-mdoc-credentials2`, `waltid-vical`, `waltid-18013-7-verifier` and the
enterprise `CredentialStatus` CWT tests - those are the suites that actually exercise negative labels, tags and
byte strings

---

## 7. Consumer-side API notes

Source-incompatible changes in the `CborElement` API that `waltid-identity` had to adapt to:

| Before                         | After                                                                             |
|--------------------------------|-----------------------------------------------------------------------------------|
| `CborByteString.value`         | `toByteArray()` (copies), or `bytes` under `@OptIn(DelicateCborApi::class)`       |
| `CborInteger.value`            | `absoluteValue` (`ULong`) plus `isPositive`; or `long` / `int` / `short` / `byte` |
| `CborElement.tags: ULongArray` | `tags: List<ULong>` - `contentEquals(ulongArrayOf(x))` becomes `== listOf(xUL)`   |

`CborString.value`, `CborBoolean.value` and `CborFloat.value` are unchanged.
