# Paket tugas Network Engineer ITCorner.id

**Penanggung jawab:** Muhammad Danish - PM & Network Engineer  
**Target branch:** `feat/network-config`  
**Versi:** 0.4 - 18 Oktober 2026  
**Status:** rancangan dan dokumentasi parsial; belum diterapkan/diuji menyeluruh di lab.

Paket ini mengisi bahan tugas jaringan: gambar topologi 13 VM, tabel IP/VLSM, panduan Edge/Internal, matriks rule, draft Suricata, dan lembar bukti uji. Baseline mengikuti RPP Final yang dibaca pada percakapan proyek; file Final asli belum tersedia di workspace saat paket disusun. Cocokkan lagi dengan file asli sebelum menamai dokumen sebagai konfigurasi final.

## Pemakaian pada PC lab 32 GB

Spesifikasi seluruh 13 VM berjumlah **48 GiB RAM**. Untuk PC 32 GB, gunakan **satu profil bergantian dengan RAM VM aktif 20-24 GiB**, menyisakan ruang nominal sekitar 8-12 GiB untuk host. Seluruh layanan tidak direncanakan menyala serentak. CPU i9-10900K dan sisa ruang kosong disk sekitar 300 GB sudah dikonfirmasi pengguna. Kinerja, jenis disk, ukuran VM aktual, serta pertumbuhan data masih harus dibuktikan di lab. Target 720 GiB disk virtual total bukan kebutuhan ruang tambahan langsung; mulai dengan data kecil dan sisakan cadangan host sekitar 50 GB.

Baca `docs/network/spesifikasi-vm-32gb.md` sebelum menyalakan VM. Dokumen itu memuat OS/mode, vCPU, RAM, disk, adapter, nama zona, profil, dan ketergantungannya. Rekam hasil di `evidence/network/uji-kapasitas-32gb.md`.

## Mulai dari tiga berkas ini

1. `docs/network/topologi-13vm.pdf` - topologi target dan alamat IP, dua halaman.
2. `docs/network/konfigurasi-edge-internal.md` - status aktual, urutan pengerjaan, dan verifikasi.
3. `config/suricata/itcorner-local.rules` - enam kandidat rules IDS, beserta batas deteksinya di panduan Suricata.

## Status yang dapat dicatat sekarang

| Pekerjaan | Status |
|---|---|
| Instalasi 13 VM | Selesai menurut konfirmasi pengguna |
| Assignment VLAN 20/30/40/50/60 Internal | Terlihat pada screenshot console |
| WAN Internal 10.10.1.2/30 | Terlihat pada screenshot console |
| LAN Management 10.10.20.1/29 | Pengguna menyatakan sudah setting; perlu cek hasil akhir |
| VLAN ID pada satu Windows | Opsi sudah muncul; tagging/koneksi belum diuji |
| Edge; routing; NAT; Internet; firewall; SOC | Perlu konfigurasi/verifikasi di lab |
| Rules Suricata dalam paket | Draft; engine dan uji lab belum dijalankan |

Paket awal menggunakan snapshot repo 15 Oktober. Saat pemasukan draf ini pada 18 Oktober 2026, branch `feat/network-config` disinkronkan ke `6820019785e345ca4770fc2b249cf8bf9510049e` melalui SSH WSL dan struktur repo diperiksa. Ini bukan audit ulang seluruh fitur aplikasi.

## Format berkas

Semua keterangan, tabel, dan catatan hasil pemeriksaan tersedia dalam `.md`. PDF tetap tersedia untuk gambar topologi. Berkas `.rules`, `.yaml`, `.json`, `.pcap`, dan `.py` merupakan konfigurasi atau bahan uji, bukan pengganti dokumentasi.

## Daftar isi

- `docs/network/tabel-ip-vlsm.md` - nama zona, subnet, VLSM, gateway, dan alokasi CPU/RAM/disk seluruh 13 VM.
- `docs/network/spesifikasi-vm-32gb.md` - spesifikasi lengkap dan enam profil penggunaan bergantian pada host 32 GB.
- `evidence/network/uji-kapasitas-32gb.md` - lembar pengukuran host dan keberhasilan tiap profil; belum diuji.
- `docs/network/firewall-rule-matrix.md` - rencana akses; bukan file impor firewall.
- `docs/network/suricata-dan-integrasi-soc.md` - SID, penempatan sensor, pemasangan, dan batas TLS/SSH.
- `docs/network/REFERENSI.md` - sumber resmi dan keputusan yang masih terbuka.
- `tests/suricata/` - PCAP sintetis offline positif/negatif, manifest ekspektasi, prosedur uji.
- `scripts/build_suricata_fixtures.py` - membangun ulang fixture lokal; tidak mengirim paket.
- `scripts/verify_suricata_alerts.py` - membandingkan EVE hasil engine dengan ekspektasi.
- `evidence/network/hasil-uji.md` - seluruh uji lab berstatus BELUM DIUJI.
- `evidence/network/validasi-paket.md` - hasil pemeriksaan statis paket, bukan bukti sistem lab berhasil.

## Memasukkan ke repository

Paket ini disimpan utuh di `network-config/` pada branch `feat/network-config`, terpisah dari implementasi aplikasi pada `itcorner-id/`. Semua path paket seperti `docs/network/...`, `config/suricata/...`, `scripts/...`, `tests/...` dan `evidence/...` dihitung relatif terhadap folder `network-config/`. Jalankan perintah uji dari folder itu ketika tahap pengujian dimulai.

Rules kandidat berada di `network-config/config/suricata/itcorner-local.rules`. Rules tim pada `itcorner-id/config/suricata/itcorner-local.rules` tidak ditimpa atau digabung secara otomatis. Pemilihan ruleset aktif, pemuatan OPNsense, dan pengujian merupakan pekerjaan tahap berikutnya. Manifest paket memakai path relatif terhadap `network-config/` dan dihitung ulang setelah penyesuaian README ini.

Tidak ada backup XML, password, private key VPN, atau token dalam paket ini. Backup konfigurasi asli disimpan privat/terenkripsi. Paket ini belum berisi XML siap restore.

## Catatan audit sebelum push draf

Pengguna menetapkan ini sebagai progres pengerjaan firewall dan IP, belum konfigurasi final. Pengujian belum dimulai. Catatan berikut sengaja belum diperbaiki pada draf ini agar tahap pekerjaan tidak disalahartikan:

- Pemeriksa `scripts/verify_suricata_alerts.py` pada kasus negatif dapat memberi PASS pada JSON biasa atau event stats tanpa bukti PCAP diproses. Jangan gunakan hasilnya sebagai acceptance sebelum pemeriksa diperbaiki dan diuji.
- Matriks firewall perlu melengkapi izin Transit Edge untuk pengelolaan Edge, akses administrasi SOC, jalur backup data Wazuh, ICMP diagnostik, serta tujuan/layanan egress sesuai kebutuhan nyata.
- Enam rules masih kandidat; parser engine, replay, pemuatan persisten OPNsense, VLAN dan integrasi live belum diuji. Paket tidak berisi XML siap restore.
- Profil VM bergantian dipakai untuk pengerjaan bertahap; belum tersedia profil seluruh alur live aplikasi sampai SOC-IR pada batas RAM ini.
- Pengujian dari luar NAT VMware memerlukan pemeriksaan port-forward VMware dan upstream, selain DNAT Edge.
- Penerusan tag dan batas isolasi guest tagging perlu dibuktikan. RPP Final asli perlu dicocokkan kembali sebelum menyatakan kesesuaian final.

Temuan tersebut merupakan backlog perbaikan, bukan hasil pengujian yang lulus. Tidak ada perubahan konfigurasi VM lab dalam commit dokumentasi ini.
