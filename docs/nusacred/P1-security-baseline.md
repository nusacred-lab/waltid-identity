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
dua build ulang dengan cache task dinonaktifkan. [CI PR strict](https://github.com/nusacred-lab/waltid-identity/actions/runs/39440757635)
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

Gerbang baseline bergantung pada hasil tes/repeatability COSE. Kegagalan job COSE
harus membuat required baseline check gagal secara eksplisit, bukan hanya skipped.
Workflow tetap read-only, tanpa hak registry, sign atau deploy. Metadata standalone
hanya berlaku pada build terisolasi module; parent build tetap memerlukan review
seluruh metadata/plugin sendiri. Temuan keamanan awal di atas tetap terbuka.

## Gerbang berikutnya

1. Pertahankan source COSE terpatok dan hasil kompatibilitasnya; perubahan source,
   dependency atau hash baru memerlukan review. Jangan menerima kembali snapshot
   tanpa verifikasi. Selesaikan bukti integrasi ke seluruh target API2.
2. Review candidate locks/checksums serta asal seluruh artefak teresolusi dan plugin;
   ulangi build strict setelah celah SNAPSHOT ditutup.
3. Scan JAR/image target, hasilkan SBOM hasil resolusi dan image, ukur freshness DB.
4. Ulangi alur credential nyata pada image fork yang sama dan rekam commit/digest.
5. Tinjau temuan inherited satu per satu; dokumentasikan pengecualian false positive
   yang spesifik dengan alasan, pemilik dan expiry jika memang dapat dibuktikan.

Scanner error, metadata tidak lengkap dan temuan yang belum ditangani menahan G1.
