# Pemeriksaan keamanan awal P1

Tanggal: 20 Oktober 2026. **G1 belum lulus.** Baseline upstream v1.2.0,
`ef516ecec4c79fd9fba6f1e8b226b52a4e8cf790`. Tidak ada pengecualian massal,
allowlist global, penghapusan riwayat atau promosi image ke produksi.

## Cakupan dan hasil

- Gitleaks 8.30.1 pada riwayat Git upstream lengkap: 2.282 temuan pada 388 path.
  Belum semua ditinjau; fixture harus dikonfirmasi per temuan sebelum pengecualian.
  Jangan menafsirkan jumlah ini sebagai jumlah credential aktif yang terbukti bocor.
- Semua 10 blob baru pada bootstrap `d7342909117e44a99ed4f9ecfa324eccc2b08083`
  diperiksa terpisah: 0 temuan. Blob lainnya identik dengan baseline upstream publik.
  Ini membolehkan publikasi perubahan non-secret, tidak meluluskan scan baseline.
- Trivy 0.76.0 source SCA: 8 target, 11 temuan High, 0 Critical pada manifest yang
  terdeteksi. Temuan di bawah berada pada dua aplikasi frontend upstream yang bukan
  target image issuer2/wallet2/verifier2. Tetap dicatat dan tidak di-ignore.
- Source CycloneDX SBOM: 239 komponen. **Belum mencakup hasil resolusi Gradle/JAR
  atau paket OS image kandidat**; jumlah komponen ini tidak membuktikan cakupan JVM.
- Laporan lengkap yang mungkin memuat token/key tetap privat. Dokumen ini hanya
  memuat ringkasan dan metadata paket publik.

## Temuan source SCA

| Target | Paket | Versi | Temuan | Severity | Perbaikan menurut database scanner |
| --- | --- | --- | --- | --- | --- |
| `waltid-applications/waltid-credentials/package-lock.json` | `node-forge` | 1.4.0 | CVE-2026-85393 | HIGH | Belum tersedia pada hasil scan |
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

## Artefak khusus dan integritas build

| Koordinat | Versi baseline | Pemeriksaan yang masih diperlukan |
| --- | --- | --- |
| `org.cose:cose-java` | `1.1.1-WALT-SNAPSHOT` | Diganti dengan project source terpatok `:third-party:cose-java`; lihat hasil perbaikan di bawah. Binary snapshot tidak diterima sebagai artefak tepercaya. |
| `id.walt:waltid-nftkit` | `1.2311291144.0` | Alias untuk web3login; validasi apakah benar masuk dependency target. Keberadaan katalog tidak membuktikan dikemas pada tiga API2. |

Penelusuran COSE pada 20 Oktober 2026 menemukan snapshot timestamp
`1.1.1-WALT-20250317.122639-2`, dipublikasikan dari
`https://maven.waltid.dev/snapshots/org/cose/cose-java/1.1.1-WALT-SNAPSHOT/`.
Binary berisi `git.properties` dengan commit
`fc897fa9da31f35c5f2e3e092496ad1c57e10457` dan **`git.dirty=true`**.
Seluruh 24 file Java source JAR cocok dengan source commit pada repo
[walt-id/cose-java](https://github.com/walt-id/cose-java/tree/fc897fa9da31f35c5f2e3e092496ad1c57e10457)
setelah normalisasi akhir baris, tanpa path hilang. Repo tersebut kini archived.

POM yang dipublikasikan berbeda dari POM commit yang diklaim: BouncyCastle
`bcprov-jdk18on`/`bcpkix-jdk18on` versi `1.80` diganti dengan
`bcprov-lts8on`/`bcpkix-lts8on` versi `2.73.7`. Binary dan source JAR tidak
memuat LICENSE/NOTICE; teks LICENSE tersedia pada commit source. Kecocokan source
belum membuktikan binary dibangun hanya dari source tersebut. Asal perubahan POM,
dependency LTS, verifikasi binary/source dan pengemasan lisensi masih harus ditangani.

SHA-256 hasil unduhan untuk penelusuran (belum menjadi checksum yang diterima
pada verification metadata rilis):

| Artefak snapshot timestamp | SHA-256 |
| --- | --- |
| Binary JAR | `f69dbdabcf8ead0b78d6d36098538f0febbfa38b07114b1965816741b671419e` |
| Source JAR | `8fc17a7c02b21a2d5326853986840ad098dfc51a53b21a5f1468c001685142a3` |
| POM | `3638b3a4df74a42dc455204a657c7b96af759650cabfc49009bf5fa5e8de2654` |

Referensi langsung `identityLibs.java.cose` ditemukan pada modul mdoc-credentials
yang digunakan issuer2; ini memerlukan pemeriksaan dependency target nyata.
`id.walt:waltid-nftkit` ditemukan pada web3login-microservice, bukan bukti masuk
classpath tiga API2. Hasil resolusi build tetap menjadi penentu akhirnya.

Repository deklaratif: Maven Central, Google, Gradle Plugin Portal,
`https://maven.waltid.dev/releases` dan `https://maven.waltid.dev/snapshots`.
Belum ada lock/verification metadata yang diterima untuk dependency target maupun
build-logic. [Bootstrap terisolasi](https://github.com/nusacred-lab/waltid-identity/actions/runs/39398624224)
pada commit `81268c0739156071a2c61626a247ed4ae748fc4a` berhasil membangun
ketiga fat JAR API2 dalam 15 menit 1 detik. Ini belum build atau uji image.
Artefak `12253803181` menghasilkan 156 lockfile dan verification metadata dengan
1.866 komponen serta 3.402 entri SHA-256. Seluruhnya masih kandidat yang belum diterima.

Review menunjukkan COSE snapshot tercatat pada lockfile ketiga API2 dan 33 lockfile
secara keseluruhan, tetapi tidak ada komponen `org.cose` pada verification metadata.
Ini sesuai keterbatasan [dependency verification Gradle](https://docs.gradle.org/current/userguide/dependency_verification.html)
untuk changing/SNAPSHOT dependency. Build 9.8.0 juga memberi peringatan bahwa
locking snapshot tidak membekukan isi artefak. Mode strict tidak boleh diklaim
melindungi artefak tersebut hanya karena metadata checksum lain sudah tersedia.

`ci/build-baseline.sh bootstrap` hanya mengumpulkan kandidat metadata;
`verify` menolak metadata yang belum tersedia dan memakai verifikasi strict.
Jangan menjalankan write-metadata pada jalur rilis untuk menerima checksum baru.

Wrapper JAR diperiksa terhadap checksum resmi:
`238e777fcddd7e34f9708186085def2abd6e08e658505b38718d79d74c21abd5`.
Distribusi Gradle 9.8.0 menggunakan SHA-256:
`bafd5ce9cfaea0fbccfdc8439a1ac42fbd4cd9c89dc9a988228d8a2639a58e6c`.
Sumber checksum: https://services.gradle.org/distributions/gradle-9.8.0-wrapper.jar.sha256
serta https://services.gradle.org/distributions/gradle-9.8.0-bin.zip.sha256.

LICENSE, NOTICE.md dan THIRD-PARTY-NOTICE.md upstream dipertahankan. Notice menyebut
867 komponen dan teks lisensi pada `LICENSES/`, tetapi direktori tersebut tidak ada
pada baseline source ini. Audit lisensi dan teks yang benar-benar dikemas pada target
masih diperlukan sebelum distribusi image. Tidak mengklaim notice statis sebagai
hasil pemeriksaan seluruh dependency rilis.

## Perbaikan COSE dari source

Perbaikan mengganti seluruh deklarasi langsung COSE (sembilan penggunaan pada
delapan file build) dengan `:third-party:cose-java`, serta menambahkan substitusi
transitif agar tidak kembali ke binary `org.cose:cose-java`. Identitas lokal:
`dev.nusacred.thirdparty:cose-java:1.1.1-fc897fa9-nusacred.1`. Semua 24 file Java
serta LICENSE sama byte demi byte dengan manifest source terpatok; implementasi
kriptografi upstream tidak ditulis ulang. LICENSE BSD-3-Clause dan provenance
dikemas dalam binary serta source JAR. Notice tambahan mempertahankan atribusi.

Module memakai BC `jdk18on` 1.86 sesuai hasil resolusi API2 sebelumnya; tidak
memasukkan LTS. CBOR 5.0.0-alpha2 dipertahankan secara eksplisit. Lombok 1.18.36
hanya untuk kompilasi/annotation processing; SLF4J API memakai katalog 2.0.20.
Lihat [keputusan dan keterbatasan module](../../third-party/cose-java/README.md).

[Discovery COSE](https://github.com/nusacred-lab/waltid-identity/actions/runs/39439984065)
meluluskan 13 tes tanpa skip dan menghasilkan binary/source JAR yang identik pada
dua build ulang dengan cache task dinonaktifkan. [CI PR strict](https://github.com/nusacred-lab/waltid-identity/actions/runs/39441236360/job/118691321626)
kemudian meluluskan job `cose-acceptance`, memakai dependency verification strict
serta locking strict tanpa menulis checksum baru. Run keseluruhan tetap gagal
pada gerbang baseline karena metadata global belum diterima; hasil job COSE saja
tidak boleh dibaca sebagai G1 lulus.

Review standalone mencocokkan 38 hash dari 20 komponen dengan unduhan terpisah
Maven Central. Lock berisi 18 koordinat termasuk dependency tes. Scan Trivy 0.76.0
mengenali 17 JAR dependency dan 18 koordinat lock (termasuk dev), tanpa temuan;
DB diperbarui 20 Oktober 2026 07:17:35 UTC. Ini bukan audit kode kriptografi atau
scan seluruh runtime/image. SBOM dependency terfokus berisi 17 komponen.

Keterbatasan upstream yang ditemukan tes: generator Ed25519 mengisi map COSE,
tetapi tidak menginisialisasi cached JCA key. Tes mengimpor serialized COSE key
melalui constructor yang memvalidasi/menginisialisasi key, lalu menguji tanda
tangan dan penolakan key lain/tamper. Bug generator langsung tidak diklaim selesai.

[Integrasi source COSE](https://github.com/nusacred-lab/waltid-identity/actions/runs/39440113754)
pada commit `78cb982f0181c997721846666c2331725d35dbaf` berhasil, durasi job
15 menit 43 detik. Ketiga fat JAR API2 dibangun, `verifyCoseReplacement`
meluluskan graph issuer/wallet/verifier tanpa binary COSE eksternal atau BC LTS,
dan tiga skenario fresh-key JVMMdocTest lulus (issuer, intermediate issuer, serta
intermediate issuer pada x5chain). Skenario itu mencakup issuance, content tamper
rejection dan presentasi dengan tanda tangan perangkat. Ini bukan uji HTTP atau
harness credential pada image. Metadata global hasil bootstrap tetap kandidat;
keberhasilan bootstrap tidak menggantikan gerbang strict. Perubahan setelah run
ini hanya menyentuh metadata/settings standalone, gerbang CI, pemeriksa manifest
dan dokumentasi; source produksi serta dependency parent build tetap sama.

Gerbang baseline bergantung pada hasil tes/repeatability COSE. Kegagalan job COSE
harus membuat required baseline check gagal secara eksplisit, bukan hanya skipped.
Workflow tetap read-only, tanpa hak registry, sign atau deploy. Metadata standalone
hanya berlaku pada build terisolasi module; parent build tetap memerlukan review
seluruh metadata/plugin sendiri. Temuan keamanan awal di atas tetap terbuka.

## Review global dan actual runtime — kelanjutan G1

[Discovery 39449623992](https://github.com/nusacred-lab/waltid-identity/actions/runs/39449623992)
pada `784162061f2b4a42c48c1423cf303afb93f0ea45` lulus build tiga API2,
graph guard COSE, tes mdoc, atribusi fat JAR, dan scan actual runtime melalui
graph hasil resolusi maupun JAR langsung. Keduanya melaporkan **nol High/Critical**
untuk masing-masing issuer, wallet dan verifier. SBOM graph berisi masing-masing
340, 405 dan 306 artefak, dicocokkan dengan SHA-256 setiap JAR. SBOM tidak
mengklaim menyimpan seluruh edge dependency transitif; daftar root mencakup
seluruh artefak runtime. Ini belum scan image atau bukti alur HTTP pada image.

Metadata global **1.872 komponen/3.431 hash** dan **159 lockfile** diterima
setelah review terpisah. Dari kandidat awal 3.398 hash: 1.626 cocok dengan
checksum repository resmi, 1.336 dengan hashing unduhan resmi, 383 dengan
pemetaan `.module` resmi lalu hashing unduhan, 52 dengan artefak custom publisher,
dan satu archive Kotlin/Native dengan digest aset release resmi JetBrains.
Sebanyak 65 hash tambahan diperiksa setelah perbaikan dependency; sebagian
menggantikan hash versi lama, sehingga jumlah final bukan 3.398 + 65.

Custom serialization `1.11.1-waltid-20260811` ditelusuri ke
[source fork `4fe61aca0dd185b0cdb920a050df81dab121cae9`](https://github.com/walt-id/kotlinx.serialization/tree/4fe61aca0dd185b0cdb920a050df81dab121cae9).
Sebanyak 946 perbandingan file kode dari source JAR lintas target cocok setelah
normalisasi akhir baris (common source berulang, bukan 946 file unik). Lisensi
dan fork notice dipertahankan persis pada `ci/licenses/kotlinx-serialization`
dan diperiksa dalam fat JAR. Tidak ditemukan attestation atau reproduksi binary;
review ini tidak mengklaim keduanya. Perilaku CBOR khusus fork dipertahankan.
Repository snapshot dihapus; repository release walt.id dibatasi pada versi
serialization itu dan koordinat NFTKit legacy spesifik, bukan mirror umum.

Runtime diperbaiki dengan Netty 4.1.138 pada issuer serta 4.2.18 pada
wallet/verifier, Jackson 2.22.3/3.2.3, json-smart 2.5.2 dan PG JDBC 42.7.14.
BC tooling 1.86 dan jose4j 0.9.6 juga dipatok. Semua hash harus mempunyai
entri review persis pada `ci/dependency-review.json`; XML, isi lock dan inventaris
lock yang berubah tanpa review ditolak. Jalur acceptance menjalankan Gradle
strict, tanpa write-metadata atau auto-promotion dari bootstrap.

[Discovery sebelumnya 39445432407](https://github.com/nusacred-lab/waltid-identity/actions/runs/39445432407)
tetap **gagal**: collector salah membaca output lifecycle `buildFatJar`.
Collector kini membaca archive `shadowJar`; kandidat parsial tanpa seluruh lock
dari run gagal tidak diimpor. Uji negatif menolak metadata/lock berubah, lock
baru tanpa review, runtime JAR berubah, serta fat JAR tanpa atribusi.

[Acceptance strict 39451595960](https://github.com/nusacred-lab/waltid-identity/actions/runs/39451595960)
**gagal** saat readiness wallet: SQLite JDBC tidak dapat menginisialisasi native
library pada temporary mount `noexec`. Probe terisolasi menggunakan JAR SQLite
3.53.2.0 yang sama dan base JRE terpatok gagal pada `noexec`, lalu berhasil pada
`exec`. Perbaikan membatasi temporary mount executable pada wallet; container
lain tetap `noexec`, root filesystem tetap read-only dan proses tanpa root.

[Acceptance strict 39454853516](https://github.com/nusacred-lab/waltid-identity/actions/runs/39454853516)
pada head `60d8c522aff10ae87537a29243ddc403ce2047b3` **berhasil**: 13 tes COSE,
tiga tes mdoc, nol gagal/error/skip, runtime/image scan nol High/Critical untuk
ketiga layanan, serta alur HTTP issuance, penyimpanan wallet, preview,
holder-bound presentation dan verifikasi nyata. Tidak ada image dipublikasikan.
[Bukti terikat source dan digest](evidence/g1-api2-39454853516.json) mencatat merge
commit yang benar-benar dibangun dan kesamaan tree dengan head PR; local image
configuration digest dibedakan dari registry manifest digest.

## Source lengkap dan remediasi lanjutan — 20–21 Oktober 2026

Scan awal belum memasukkan seluruh development dependencies frontend.
`--include-dev-deps` kini diwajibkan pada source scan/SBOM. Cakupan lengkap pada
lock awal melaporkan **213 High/15 Critical**; angka ini tidak boleh dianggap
sebagai temuan yang dikemas pada tiga actual runtime API2.

Aturan patch pada init build memperbaiki classpath compile/plugin yang juga
rentan, mempertahankan minor family Jackson/Netty dan tidak menurunkan versi.
BOM service API2 tetap independen. Discovery hanya memperbarui keluarga lock yang
ditargetkan; jalur strict tidak memakai update-locks atau write-metadata.
[Discovery 39459390656](https://github.com/nusacred-lab/waltid-identity/actions/runs/39459390656)
berhasil termasuk image dan credential flow. **35 hash tambahan** diperiksa
terpisah; metadata diterima berisi **1.894 komponen/3.466 hash dan 159 lockfile**.
Scan seluruh kandidat lock Gradle, termasuk dev, melaporkan nol High/Critical.

Ketiga graph frontend diperbarui dengan strict peer validation dan 1.270 arsip
npm direview terhadap metadata registry serta byte unduhan terpisah. Bundled
component dan perbedaan root direktori arsip DefinitelyTyped juga diperiksa.
Npm 10 mengalami error internal; npm 11.21.1 yang integritasnya diperiksa berhasil
melakukan resolusi strict tanpa legacy-peer-deps. Toolchain builder Node, header
native dan npm dipatok. Script lifecycle/build berjalan tanpa jaringan setelah
instalasi arsip tanpa script. [Rincian dan batas cakupan](../../ci/FRONTEND-BASELINE.md).

Migrasi awal Content belum mencakup seluruh navigasi/API dan ditolak tes SSR
pada [run 39460484815](https://github.com/nusacred-lab/waltid-identity/actions/runs/39460484815).
Perbaikan melengkapi navigasi, surrounding pages, TOC dan endpoint JSON menggunakan
codec AST resmi yang sudah direview. Uji HTTP lokal terisolasi pada build nyata
kemudian meluluskan halaman root/nested, target TOC, navigasi, 404 halaman hilang,
tiga API credential yang cocok dengan Markdown sumber dan menolak nama tak ada,
serta API mapping/manifest pada fixture sintetis versioned. CI untuk revisi final
wajib mengulang build frontend dan acceptance API2 sebelum perubahan diterima.

Scan source lengkap setelah lock hasil review diterapkan melaporkan **4 High,
0 Critical**: `node-forge` 1.4.0 / CVE-2026-85393 dan `braces` 3.0.3 /
CVE-2026-93687 pada dua frontend. Registry resmi belum menyediakan versi perbaikan
saat diperiksa. Dependency review GitHub juga menolak braces. Tidak ada waiver,
ignore atau perubahan namespace package agar scanner kehilangan temuan.

Riwayat masih mempunyai 2.282 temuan, dikelompokkan secara privat menjadi 361
nilai berbeda untuk triase. Pengelompokan bukan bukti false positive atau
credential aktif. Tiga kelompok AWS/Azure belum mempunyai konfirmasi
fixture/revocation. Tidak ada percobaan autentikasi atau laporan publik atas
nilai tersebut. **G1 tetap belum lulus.**

## Gerbang berikutnya

1. Pertahankan source COSE, ledger review dan hasil kompatibilitas; dependency
   atau hash baru memerlukan review, termasuk perubahan inventaris lock.
2. Buktikan jalur strict tanpa perubahan metadata, termasuk tes tanpa skip.
3. Luluskan scan image dan alur credential nyata pada image yang sama; rekam
   source/JAR/base digest serta local image configuration digest dengan jenis
   digest yang tepat. Tidak ada publikasi registry pada workflow ini.
4. Tangani temuan source/frontend dan riwayat inherited satu per satu. Required
   security harus menahan kegagalan keduanya. Tidak ada pengecualian massal.

Scanner error, metadata tidak lengkap dan temuan yang belum ditangani menahan G1.
