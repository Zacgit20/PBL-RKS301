# Referensi dan batas pemeriksaan

Tanggal riset 18 Oktober 2026. Baseline berasal dari RPP Final yang sebelumnya dibaca dan handover 17 Oktober. Dokumen Final asli perlu dicocokkan kembali; file sumber sinkronisasi tidak diubah.

| Sumber | Kegunaan |
|---|---|
| https://docs.opnsense.org/manual/how-tos/vlan_and_lagg.html | Parent, VLAN, trunk/access, gateway antar-VLAN |
| https://docs.opnsense.org/manual/backups.html | Backup/restore XML dan penyesuaian interface |
| https://docs.opnsense.org/manual/ips.html | Mode IDS/IPS, capture, rules, EVE syslog, opsi custom |
| https://docs.suricata.io/en/suricata-7.0.10/rules/http-keywords.html | Sticky buffer URI/body; normalisasi URI |
| https://docs.suricata.io/en/suricata-7.0.10/rules/thresholding.html | detection_filter dan threshold |
| https://docs.suricata.io/en/suricata-7.0.10/command-line-options.html | -T, -S, -r, log output |
| https://docs.suricata.io/en/suricata-7.0.10/rules/ssh-keywords.html | Metadata SSH yang terlihat sensor |
| https://raw.githubusercontent.com/opnsense/core/master/src/opnsense/service/templates/OPNsense/IDS/suricata.yaml | Source template saat riset; bukan kepastian isi versi lab |

## Keputusan yang masih terbuka

1. Versi Workstation lab, IP/gateway/DNS upstream Edge, dan pemetaan adapter Edge.
2. Hasil akhir LAN Management dan pengisian IP OPT di Internal.
3. Pembuktian penerusan tag VLAN pada LAN Segment dan batas isolasi guest tagging.
4. DNS/NTP, alias egress, dan rule AD/backup sesuai layanan aktual.
5. Versi Suricata lab, metode custom rules persisten, titik observasi plaintext, dan tuning threshold.
6. Verifikasi semua langkah melalui evidence; belum ada XML yang siap restore.

Rules menggunakan keyword yang didokumentasikan Suricata 7.0.10; bukan klaim engine lab memakai versi itu. Daftar hasil uji lab sengaja belum diberi PASS. Gambar topologi sekarang berasal dari RPP perbaikan dan belum menampilkan Bastion (ditiadakan pada Rev.3). Gambar ini merupakan acuan dokumen, bukan hasil discovery atau bukti semua jalur aktif.

## Sumber kapasitas VM - revisi 0.3

Sumber diperiksa 18 Oktober 2026. Angka pada tabel VM adalah usulan lab berdasarkan kebutuhan layanan; bukan semua merupakan minimum resmi vendor.

| Sumber resmi | Dasar keputusan |
| --- | --- |
| [OPNsense hardware sizing](https://docs.opnsense.org/manual/hardware.html) | Kelas reasonable 4 GB RAM / 40 GB SSD untuk beban ringan; IDS/IPS memerlukan pengukuran. |
| [Wazuh quickstart](https://documentation.wazuh.com/current/quickstart.html) | All-in-one 1-25 agent: rekomendasi 4 vCPU, 8 GiB RAM, storage 50 GB. |
| [TheHive system requirements](https://docs.strangebee.com/thehive/installation/system-requirements/) | Profil Docker Compose testing TheHive/Cortex beserta dependency: 8 GB, 4 vCPU; berbeda dari produksi. |
| [MISP performance tuning](https://www.misp-project.org/misp-performance-tuning/) | Penggunaan kecil dapat memakai 4 GB; data, pengguna, worker dan IOPS mengubah kebutuhan. |
| [Windows 11 specifications](https://www.microsoft.com/en-us/windows/windows-11-specifications) | RAM 4 GB, storage 64 GB, CPU kompatibel minimal dua core, UEFI dan TPM 2.0. |
| [Windows Server requirements](https://learn.microsoft.com/en-us/windows-server/get-started/hardware-requirements) | Periksa kebutuhan OS dan role AD/DNS; ukuran praktikum tetap harus diuji. |

**Pembaruan 0.4:** pengguna mengonfirmasi CPU i9-10900K, RAM 32 GB dan sisa ruang kosong sekitar 300 GB pada 18 Oktober 2026. Angka 300 GB bukan kapasitas total disk.

Keputusan kapasitas yang masih terbuka: RAM usable/pemakaian host, kapasitas total/jenis disk, ukuran VM aktual dan pertumbuhan data, versi guest dan container, pemakaian RAM SOC-IR gabungan, serta apakah penilaian mensyaratkan seluruh 12 VM live bersamaan. Total 48 GiB dan batas profil 24 GiB adalah hitungan alokasi, bukan hasil benchmark. Lihat [rencana kapasitas](spesifikasi-vm-32gb.md).

## Revisi 0.5 - target IPS dan rencana bukti

Tim menetapkan target akhir Suricata IPS pada Edge dan Internal. Kandidat Netmap, parent trunk, perubahan aksi efektif terpilih, keterbatasan EVE syslog dan langkah rollback mengikuti sumber resmi, lalu harus diverifikasi terhadap versi lab. Rancangan endpoint, pemilihan SID dan profil P7 merupakan keputusan praktikum, bukan jaminan vendor.

| Sumber resmi | Penggunaan pada revisi IPS |
| --- | --- |
| [OPNsense IPS](https://docs.opnsense.org/manual/ips.html) | Capture mode, parent Netmap, offloading, aksi rule dan batas pengiriman drop logs melalui syslog. |
| [Suricata thresholding 7.0.10](https://docs.suricata.io/en/suricata-7.0.10/rules/thresholding.html) | Perbedaan threshold dan detection_filter; jangan menebak perilaku drop versi lab. |
| [Suricata EVE JSON output 7.0.10](https://docs.suricata.io/en/suricata-7.0.10/output/eve/eve-json-output.html) | Kategori log alert/drop lokal dan pemilihan output; bukan kepastian semua record diteruskan OPNsense. |

Keputusan yang belum selesai: driver dan mode inline lab, parent Edge, pemuatan custom rules persisten, SID drop yang lulus tuning, metode bukti/koleksi drop lokal, resource IPS, jalur normal serta rollback. Status implementasi dan pengujian tidak berubah menjadi selesai karena revisi dokumen.

## Revisi 0.6 - sumber gambar topologi

Gambar diambil dari RPP PBL RKS-301 perbaikan.docx, bagian Desain Umum, media word/media/image1.png. File PNG dipertahankan tanpa menggambar ulang. Sumber lokal tersebut masih memuat rancangan 12 VM dan belum menggambarkan Bastion (ditiadakan pada Rev.3); daftar target 12 VM tetap dipertahankan sesuai arahan terbaru. RPP Final asli belum tersedia untuk dicocokkan. Identitas dan hash sumber ada di [topologi-rpp.md](topologi-rpp.md), dengan catatan ekstraksi pada validasi paket.
