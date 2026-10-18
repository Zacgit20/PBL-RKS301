# Rencana Suricata IPS pada OPNsense Edge dan Internal

**Versi:** 0.5 - 18 Oktober 2026  
**PIC Network:** Muhammad Danish  
**Koordinasi SOC:** Nur Arsyika Juana  
**Status:** TARGET IPS; konfigurasi firewall/IP masih dikerjakan; IPS dan pengujian belum diterapkan.

## 1. Tujuan dan kondisi saat ini

Tim menetapkan Suricata sebagai Intrusion Prevention System (IPS) pada Edge dan Internal OPNsense. Targetnya mendeteksi serta memblokir trafik yang cocok dengan rules terpilih, lalu menyediakan event yang bisa ditelusuri tim SOC. Firewall tetap menentukan akses antarzona; IPS memeriksa trafik yang benar-benar melewati sensor. Layanan WAF tetap digunakan untuk perlindungan aplikasi HTTPS.

Enam rules kandidat dalam paket masih memakai aksi `alert`. Ini baseline observasi untuk persiapan IPS, bukan bukti IPS aktif. Dokumen ini tidak mengubah rules, YAML, PCAP, VM lab atau policy yang sedang berjalan. Metode pemuatan rules persisten pada versi lab masih harus diverifikasi. Tidak ada XML siap restore.

## 2. Tahapan pengerjaan

| Tahap | Target | Syarat melanjutkan | Kondisi sekarang |
| --- | --- | --- | --- |
| A - Jaringan | IP, VLAN, routing, NAT dan aturan firewall sesuai kebutuhan | Jalur normal serta akses pemulihan console tersedia | Sedang dikerjakan |
| B - Observasi | Parser rules, uji normal dan trafik uji dalam mode alert | Keenam SID dimuat; sumber event dan false positive dipahami | BELUM DIUJI |
| C - IPS terbatas | Mode inline dan aksi drop pada satu SID kandidat terlebih dahulu | Trafik normal lolos; trafik uji yang sesuai diblokir oleh IPS | BELUM DITERAPKAN / BELUM DIUJI |
| D - Perluasan | Tambah SID/interface secara bertahap setelah tuning | Resource, logging, persistensi dan rollback terverifikasi | BELUM DITERAPKAN / BELUM DIUJI |

Tahap observasi tetap diperlukan walaupun target akhir IPS. Jangan mengubah seluruh rule menjadi drop sekaligus atau menganggap mode IPS saja sudah membuat rule alert memblokir.

## 3. Mode dan titik inspeksi target

Mode awal yang direncanakan untuk dievaluasi adalah **Netmap IPS**, mengikuti kemampuan NIC/driver guest yang nyata. Untuk VLAN, panduan OPNsense menempatkan Netmap IPS pada parent interface. Nama adapter Edge belum dipastikan; jangan menyalin pemetaan em0/em1 Internal ke Edge. [OPNsense IPS](https://docs.opnsense.org/manual/ips.html).

| Firewall | Titik target | Cakupan / pemeriksaan yang diperlukan |
| --- | --- | --- |
| Edge | Parent trunk DMZ yang membawa VLAN 10; nama NIC belum dicatat | Trafik menuju/dari Web dan Bastion yang melewati Edge; cocokkan MAC, tag dan IP tujuan yang terlihat setelah NAT |
| Internal | Parent trunk `em1` yang membawa VLAN 20/30/40/50/60 | Trafik yang dirutekan melalui Internal; bukan child `em1_vlan20` dan seterusnya untuk pilihan Netmap ini |
| Keduanya | Parent yang didukung driver dan benar-benar dilewati trafik | Periksa duplikasi ketika satu alur terlihat di beberapa interface/firewall; catat identitas sensor dan flow |

Jangan memilih semua interface tanpa menguji jalur. Trafik langsung sesama VLAN/subnet tidak otomatis melewati router, sehingga tidak dijamin diperiksa oleh IPS di firewall. Kontrol host dan batas isolasi guest tagging tetap mengikuti dokumen jaringan.

OPNsense juga mendokumentasikan Divert IPS dengan aturan `divert-to` pada Rules [new]. Pilihan itu merupakan alternatif desain bila diperlukan; belum dipilih, dikonfigurasi atau diuji pada lab. Kegagalan Netmap tidak boleh dilaporkan sebagai IPS berhasil hanya karena mode IDS dapat berjalan.

## 4. Checklist konfigurasi saat tahap lab dimulai

1. Catat versi OPNsense/Suricata, jenis NIC, driver, MAC, interface, IP dan jalur trafik. Siapkan backup privat, akses console dan rencana pengembalian konfigurasi.
2. Selesaikan aturan firewall dan konektivitas normal. Tetapkan HOME_NET untuk subnet proyek yang diperiksa; periksa hubungan dengan EXTERNAL_NET agar trafik uji dari jaringan proyek sendiri tidak terlewat karena definisi yang keliru.
3. Verifikasi pemuatan custom rules yang persisten tanpa menimpa ruleset tim lain. Simpan daftar SID, hash file, konfigurasi efektif dan hasil parser engine. Jalur rules paket dan implementasi `itcorner-id/` berbeda; jangan memuat keduanya tanpa inventaris.
4. Sebelum Netmap IPS, periksa dan nonaktifkan hardware offloading sesuai panduan OPNsense, termasuk checksum/segmentation offload dan VLAN hardware filtering bila tersedia. Catat perubahan dan uji ulang penerusan tag; jangan menebak dukungan driver. [Panduan pengaturan IPS](https://docs.opnsense.org/manual/ips.html).
5. Lakukan observasi dengan rules alert, trafik normal dan trafik uji yang diizinkan. Periksa penggunaan RAM/CPU, error/drop packet akibat resource, serta sumber event yang diterima SOC.
6. Setelah itu aktifkan mode inline yang dipilih dan ubah **aksi efektif SID terpilih** menjadi drop. Gunakan pengaturan rule/policy OPNsense yang mendukung ruleset tersebut; periksa Installed rules dan hasil render, bukan hanya label menu. Rules baseline pada Git dapat tetap alert; override drop yang dipakai lab harus didokumentasikan dengan SID, scope, waktu dan rollback.
7. Uji satu SID dan satu sensor dahulu. Tambahkan scope setelah trafik normal, drop aktual dan pemulihan terbukti. Bila isi file rule diubah pada tahap berikutnya, naikkan revision dan ulangi parser/tuning.
8. Periksa persistensi setelah Apply/restart. Jika hasil uji belum ada, status tetap BELUM DIUJI.

## 5. Rencana aksi keenam SID

| SID | Pola | Tahap observasi | Aksi target IPS setelah validasi | Batas |
| --- | --- | --- | --- | --- |
| 1003001 | UNION SELECT pada URI HTTP | alert | Kandidat drop terpilih | Harus terlihat plaintext; pola SQLi terbatas |
| 1003002 | Awalan script pada URI HTTP | alert | Kandidat drop terpilih | Tuning terhadap input sah; bukan semua XSS |
| 1003003 | UNION SELECT pada request body | alert | Kandidat drop terpilih | Parser/body limit/encoding harus sesuai trafik nyata |
| 1003004 | Awalan script pada request body | alert | Kandidat drop terpilih | Tuning encoding dan false positive |
| 1003005 | POST /login berulang | alert | Tetap alert pada rancangan awal IPS | Tidak membuktikan login gagal; sumber dapat tergabung oleh NAT/proxy |
| 1003006 | SYN SSH berulang ke Bastion | alert | Tetap alert pada rancangan awal IPS | Tidak membaca password SSH; retransmission dan koneksi sah bisa menambah hitungan |

Mekanisme alert threshold bukan selalu mekanisme menunda drop. Dokumentasi Suricata 7.0.10 membedakan `threshold` dengan `detection_filter`: aksi drop pada threshold diterapkan pada kecocokan paket, sedangkan detection_filter dikaitkan dengan kecocokan yang menghasilkan alert. Jangan menyimpulkan semantik versi lain tanpa uji engine aktual. SID 1003005/1003006 tetap alert sambil dikorelasikan dengan log autentikasi; rancangan rate limiting/blokir brute force memerlukan keputusan terpisah. [Suricata thresholding](https://docs.suricata.io/en/suricata-7.0.10/rules/thresholding.html).

## 6. HTTPS dan pembuktian drop

Mode IPS tidak otomatis mendekripsi HTTPS. SQLi/XSS pada aplikasi HTTPS ditangani dan dicatat WAF. Untuk menguji rules HTTP Suricata, gunakan endpoint HTTP lab terbatas yang benar-benar melewati sensor, atau evaluasi signature lain yang sesuai protokol terlihat. Jangan membuka HTTP publik atau menonaktifkan HTTPS aplikasi demi demo.

Skenario HTTP lab sementara mengikuti T01: Kali ke Web TCP 8080, hanya setelah listener dan izin jalurnya tersedia. Trafik normal pada jalur yang sama harus berhasil sebelum menguji pola kandidat. Bila koneksi sudah ditolak firewall atau WAF, kegagalan request belum membuktikan IPS bekerja.

Untuk menyatakan LULUS IPS, gabungkan bukti mode inline dan aksi efektif drop, SID/waktu/flow pada log lokal, capture sebelum/sesudah sensor, serta pengamatan endpoint. Bagian payload yang diblokir tidak boleh diteruskan lengkap; paket handshake yang lebih dulu terlihat di server tidak otomatis berarti IPS gagal. Timeout atau screenshot alert saja tidak cukup. Catat juga trafik normal yang tetap lolos, false positive, dan hasil rollback. Replay PCAP offline hanya memeriksa parsing/deteksi; tidak membuktikan pemblokiran live.

## 7. Logging dan koordinasi SOC

Simpan identitas firewall/sensor, interface, versi, SID/rev, aksi efektif, timestamp, src/dest, flow ID jika tersedia, dan lokasi log/bukti endpoint. Catat apakah keputusan berasal dari IPS, firewall atau WAF. Format field EVE harus mengikuti output versi aktual; jangan menyatakan field tertentu pasti tersedia.

OPNsense mendokumentasikan EVE syslog untuk alert, dengan catatan drop logs dikirim ke logger internal. Karena itu jangan menganggap seluruh record drop otomatis terkirim lewat EVE syslog ke Wazuh. Verifikasi event alert yang diterima SOC dan ambil bukti drop lokal melalui metode koleksi yang didukung. Untuk raw record drop, tentukan mekanisme terpisah bersama SOC dan uji; tidak perlu mengasumsikan Wazuh Agent dapat langsung dipasang pada OPNsense. [OPNsense logging IPS](https://docs.opnsense.org/manual/ips.html).

Tim SOC menelusuri event ke Wazuh lalu case TheHive bila skenario integrasi dijalankan. Bila SOC-IR mati karena profil RAM, catat batas tahap tersebut; keberhasilan drop tidak otomatis berarti seluruh alur SOC sudah berhasil.

## 8. Resource dan rollback

Tambahan fitur IPS belum memiliki hasil benchmark lab. Anggaran awal firewall tetap 4 GiB per VM untuk dicoba dengan rules terbatas; tambahkan resource atau kurangi VM aktif bila tidak cukup. Gunakan profil P7 pada [spesifikasi VM](spesifikasi-vm-32gb.md): Edge, Internal, Web/App, Database, Wazuh dan Kali, total 22 GiB RAM VM. SOC-IR, DC dan client lain mati; DNS/domain serta alur TheHive tidak tercakup. Jangan menjalankan profil lain bersamaan.

Rollback awal mengembalikan aksi SID uji dari drop ke alert, lalu memeriksa layanan normal. Jika gangguan membuat pengelolaan jaringan terputus, gunakan console dan pulihkan konfigurasi Suricata/interface dari catatan/backup; jangan mematikan seluruh firewall. Catat apakah layanan pulih dan simpan evidence sebelum mengakhiri sesi.

Lembar pengujian IPS-01 sampai IPS-08 tersedia pada [hasil-uji.md](../../evidence/network/hasil-uji.md). Semua status awal BELUM DIUJI. Pembaruan dokumen ini bukan implementasi IPS pada VM lab.
