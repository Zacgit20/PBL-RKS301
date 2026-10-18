# Konfigurasi Edge dan Internal Firewall

Penanggung jawab: Muhammad Danish. Versi 0.5, 18 Oktober 2026. Dokumen berisi target dan langkah kerja; status aktual dipisahkan dari target. Target keamanan jaringan adalah Suricata IPS pada kedua firewall; pemblokiran belum diterapkan.

## 1. Kondisi terakhir yang diketahui

Lab memakai VMware Workstation, versinya belum diketahui. Console Internal menampilkan OPNsense 26.7 amd64. Workstation komputer rumah pernah terbaca 17.6.4; jangan menyamakan keduanya. Semua 13 VM sudah diinstal menurut pengguna.

| Peran | Interface Internal | MAC lab | LAN Segment | Target IP | Bukti terakhir |
|---|---|---|---|---|---|
| Transit/WAN | em0 | 00:0c:29:fb:c4:79 | PBL-TRANSIT | 10.10.1.2/30 | IP terlihat di console |
| Parent trunk | em1 | 00:0c:29:fb:c4:83 | PBL-TRUNK-INTERNAL | Tidak diberi IP | Pemetaan dikonfirmasi pengguna |
| LAN Management | em1_vlan20 | Mengikuti parent | Trunk tag 20 | 10.10.20.1/29 | Pengisian dilaporkan; perlu cek screenshot akhir |
| OPT1 Server | em1_vlan30 | Mengikuti parent | Trunk tag 30 | 10.10.30.1/29 | Assignment terlihat; IP belum dikonfirmasi |
| OPT2 SOC | em1_vlan40 | Mengikuti parent | Trunk tag 40 | 10.10.40.1/29 | Assignment terlihat; IP belum dikonfirmasi |
| OPT3 Client | em1_vlan50 | Mengikuti parent | Trunk tag 50 | 10.10.50.1/27 | Assignment terlihat; IP belum dikonfirmasi |
| OPT4 Testing | em1_vlan60 | Mengikuti parent | Trunk tag 60 | 10.10.60.1/30 | Assignment terlihat; IP belum dikonfirmasi |

Gateway WAN diarahkan ke 10.10.1.1 dan penggunaan gateway sebagai DNS dipandu dijawab tidak; verifikasi nilai akhirnya. Tidak ada hasil ping, web GUI, routing, NAT, atau VLAN capture yang membuktikan keberhasilan integrasi.

## 2. Pemetaan VMware target

| VM/adapter | Media | Fungsi |
|---|---|---|
| Edge WAN | NAT VMware, atau upstream lab yang disepakati | Internet; alamat/gateway dari upstream |
| Edge Transit | PBL-TRANSIT | 10.10.1.1/30, tanpa tag VLAN |
| Edge parent DMZ | PBL-TRUNK-DMZ | Parent tanpa IP; child VLAN 10 memakai 10.10.10.1/29 |
| Internal Transit | PBL-TRANSIT | em0, 10.10.1.2/30 |
| Internal trunk | PBL-TRUNK-INTERNAL | em1, VLAN 20/30/40/50/60 |
| Web/App dan Bastion | PBL-TRUNK-DMZ | Guest melakukan tagging VLAN 10 |
| VM internal lainnya | PBL-TRUNK-INTERNAL | Guest melakukan tagging sesuai zona |

Nama PBL-TRUNK-DMZ adalah nama target yang baru disarankan; belum dikonfirmasi ada di lab. Jangan mengganti nama/koneksi yang sudah ada tanpa mencocokkan MAC dan fungsi adapter. Nama interface Edge belum diketahui. MAC lab tidak perlu disalin ke rumah.

LAN Segment hanyalah penghubung virtual. Pilihan ini membutuhkan tag 802.1Q pada guest dan firewall. Uji dengan satu host lebih dulu. Guest yang bisa mengganti tag pada media bersama tidak dikunci oleh access-port; ini keterbatasan rancangan yang harus dibahas dengan tim/manajer. Jangan menyebut isolasinya setara managed switch. Jika dibutuhkan kontrol access-port, evaluasi switch VLAN-aware sebelum mengubah jumlah VM.

## 3. Urutan konfigurasi Internal

1. Pastikan console VMware bisa diakses; ambil backup bila sudah ada konfigurasi.
2. Cocokkan adapter lewat MAC. Pertahankan em0 Transit dan em1 trunk yang sudah dikonfirmasi.
3. Periksa lima VLAN dan assignment. Jangan membuat VLAN duplikat.
4. Atur WAN static 10.10.1.2/30, gateway 10.10.1.1. Pilih tidak memakai gateway sebagai DNS sampai layanan DNS tersebut memang tersedia.
5. Atur alamat gateway setiap VLAN sesuai tabel. Tidak ada upstream gateway pada child VLAN internal. Untuk tahap awal gunakan IPv4 statis dan DHCP nonaktif pada subnet server/management; kebijakan IPv6 ditetapkan terpisah.
6. Parent em1 tetap tanpa IP. Periksa alamat lama 192.168.1.1/24 tidak lagi dipakai sebagai LAN final.
7. Siapkan Management 10.10.20.2/29 dengan tag 20. Dari host ini, uji gateway dan akses HTTPS 10.10.20.1 melalui rule administrasi yang tepat. Jangan menganggap Win11 pada VLAN 50 boleh mengelola firewall.
8. Pada WAN privat Internal, tinjau opsi Block private networks. Nonaktifkan opsi tersebut untuk interface transit privat jika aktif, lalu gunakan rule transit spesifik sesuai matriks. Tidak perlu mematikan seluruh firewall.
9. Ganti rule LAN default allow-any dengan akses yang diperlukan setelah akses admin spesifik diuji. Pertahankan pemulihan console dan periksa anti-lockout agar akses GUI tidak terputus.
10. Terapkan rule per interface masuk, lalu uji allow dan deny dari host yang benar. Pemeriksaan stateful tidak membutuhkan rule balik simetris untuk koneksi yang sama.

## 4. Urutan konfigurasi Edge

1. Periksa tiga adapter dan MAC aktual. Pemetaan em0/em1 Internal tidak boleh diasumsikan berlaku pada Edge.
2. WAN menggunakan upstream yang disetujui, misalnya NAT VMware. Jika upstream privat, tinjau Block private networks pada WAN dan cakupan rule WAN; jangan mengaktifkan akses admin dari seluruh WAN.
3. Transit diberi 10.10.1.1/30. Parent DMZ tanpa IP, child VLAN 10 diberi 10.10.10.1/29.
4. Tambahkan gateway transit ke Internal 10.10.1.2. Jika monitoring gateway dipakai, pastikan probe/rule tersedia; status monitor gagal bukan alasan menonaktifkan firewall.
5. Tambahkan lima static route: 10.10.20.0/29, 10.10.30.0/29, 10.10.40.0/29, 10.10.50.0/27, 10.10.60.0/30, semuanya via 10.10.1.2.
6. Periksa routing sebelum mengatur DNAT. Web/App tetap IP privat 10.10.10.2.
7. Setelah HTTPS aplikasi siap, DNAT WAN TCP 443 ke 10.10.10.2 TCP 443 dengan filter terkait. Jangan memublikasikan SSH, PostgreSQL, RDP, atau dashboard SOC.
8. Buat WireGuard 10.10.70.1/29 setelah akun/peer/rute admin disepakati. Aktifkan UDP 51820 di WAN hanya saat konfigurasi tunnel siap. Peer .2-.6 adalah alokasi; izinkan peer yang benar-benar terdaftar.

## 5. NAT dan jalur pulang

Internal berfungsi sebagai router antar-zona. Audit rule outbound NAT otomatisnya; targetnya tidak menerjemahkan trafik VLAN internal menuju Edge/DMZ. Pilih konfigurasi outbound NAT yang mempertahankan source IP sesuai desain, dan buktikan dengan capture. Jangan mengandalkan NAT untuk menggantikan static route balik di Edge.

Di Edge, inventaris rule NAT yang ada, lalu tambahkan outbound NAT hanya untuk subnet yang memang diberi akses Internet. Firewall tetap membatasi tujuan/port. Periksa subnet di belakang Internal karena automatic NAT belum tentu mengenal semuanya. Trafik DMZ/Transit menuju jaringan internal tidak boleh terkena NAT Internet.

Tidak ada nilai IP WAN atau daftar DNS/NTP egress yang dapat diisi secara pasti sebelum upstream lab diketahui. Catat alias target, resolver, layanan paket, GitHub/GHCR, dan dependensi yang disetujui; jangan membuat allow-any permanen.

## 6. Windows dan Linux guest tagging

Satu VM Windows awalnya memakai Intel 82574L dengan driver Microsoft dan tidak memiliki VLAN ID. VMware Tools sudah terpasang. Setelah dipandu memakai VMXNET3, pengguna mengonfirmasi opsi VLAN ID muncul. Belum ada bukti kedua Windows sudah diubah atau tagging berhasil.

Windows Server: tag 30, IP 10.10.30.4/29, gateway 10.10.30.1. Windows 11: tag 50, IP 10.10.50.10/27, gateway 10.10.50.1. Verifikasi konfigurasi adapter yang benar; catat IP/DNS sebelum perubahan. Jika mengganti jenis adapter, shutdown normal dan backup .vmx; jangan menghapus lock file milik VM aktif.

Linux membuat child VLAN pada NIC yang terhubung ke LAN Segment yang sesuai. Nama NIC, renderer, dan lokasi konfigurasi harus mengikuti OS aktual. IP dipasang pada child VLAN; jangan menaruh IP subnet yang sama sekaligus pada parent dan child. Web/App dan Bastion juga memerlukan tag 10 pada desain ini.

## 7. Bukti minimum sebelum menyebut tahap jaringan selesai

- Capture menunjukkan VLAN tag sesuai pada jalur trunk; gateway merespons dari host zonanya.
- Akses Management ke GUI diperiksa; akses admin dari zona lain mengikuti kebijakan.
- Route dua arah Edge/Internal bekerja dengan source IP terjaga.
- Rule Web/App ke PostgreSQL berfungsi, dan percobaan dari Client langsung ke DB ditolak dengan evidence.
- NAT Internet, DNS, dan HTTPS publik diuji dari posisi jaringan yang benar.
- Uji sesama VLAN memakai kontrol host bila diperlukan; router tidak melihat trafik langsung sesama subnet.
- Isi hasil-uji.md dengan hasil aktual, waktu, pelaksana, serta tautan bukti.

## 8. Konfigurasi di rumah dan XML ke lab

Siapkan dua VM firewall dengan versi yang sesuai lab dan pemetaan interface yang dicatat. Export lewat System > Configuration > Backups. Simpan Edge dan Internal sebagai file terpisah, privat/terenkripsi. XML membawa konfigurasi termasuk akun/sertifikat; bukan konfigurasi LAN Segment, driver guest, atau instalasi plugin.

Di lab, backup terlebih dahulu, pertahankan console, restore ke firewall yang tepat, cocokkan interface, lalu uji. Full restore dapat mengganti kredensial/sertifikat. Paket ini tidak menyediakan XML hasil tebakan. Backup nyata dan uji restore belum tersedia.

## 9. Tahap Suricata IPS setelah IP dan firewall siap

Ikuti [rencana IPS](rencana-ips-opnsense.md). Evaluasi Netmap IPS pada parent trunk Internal `em1` dan parent DMZ Edge yang sudah dicocokkan ke MAC; jangan menebak nama adapter Edge. Periksa driver, hardware offloading dan penerusan VLAN. Alternatif mode lain memerlukan rancangan tersendiri.

Selesaikan observasi alert dan tuning sebelum mengaktifkan drop SID terpilih. IPS membutuhkan mode inline dan aksi efektif drop; keberadaan file rules tidak membuktikan keduanya aktif. Periksa trafik normal, bukti drop lokal, endpoint, resource, persistensi dan rollback. Mode IPS tidak mendekripsi HTTPS. Status tahap ini BELUM DITERAPKAN / BELUM DIUJI.

## Referensi

- https://docs.opnsense.org/manual/how-tos/vlan_and_lagg.html
- https://docs.opnsense.org/manual/backups.html
- https://docs.opnsense.org/manual/ips.html
