# Validasi paket Network Config ITCorner

Validasi paket Network Config ITCorner - 18 Oktober 2026

Pemeriksaan yang sudah dilakukan pembuat paket:
- 13 entri VM: IP unik, prefix tepat, host berada dalam subnet: PASS (data statis).
- 8 subnet: tidak overlap, netmask dan kapasitas usable tepat: PASS (data statis).
- 6 SID unik 1003001-1003006, aksi alert, kutip dasar: PASS (pemeriksaan teks; bukan parser Suricata).
- Dua script Python dapat dikompilasi: PASS.
- Utility pembaca EVE diuji dengan 5 kasus sintetis: PASS, termasuk menolak missing SID, alert negatif, dan file kosong.
- PCAP sintetis: positive 128 frame dan negative 32 frame; panjang record/header, checksum IPv4 dan TCP: PASS.
- PDF 2 halaman dibuka, alamat seluruh VM ditemukan dalam teks, dan PNG tiap halaman diperiksa secara visual: PASS.
- Lembar uji Markdown: 20 skenario, seluruh status BELUM DIUJI, hasil aktual belum dicatat: PASS (integritas pencatatan).

Pemeriksaan yang BELUM dilakukan:
- suricata -T dan pengujian keyword pada engine: BELUM DIJALANKAN.
- Replay positive/negative pada Suricata: BELUM DIJALANKAN.
- Uji live OPNsense, pemuatan rule persisten, VLAN, route, NAT, Wazuh: BELUM DIUJI.
- Pembuatan XML backup atau uji restore: BELUM DILAKUKAN.

Batas lingkungan: binary Suricata tidak tersedia langsung; Docker Linux engine tidak berjalan; akses WSL ditolak lingkungan eksekusi. Tidak ada software/plugin yang dipasang atau layanan host yang diubah.

Catatan: hasil statis dan fixture sintetis bukan evidence lab. Tidak ada screenshot/alert/case ID lab buatan. Pada pemeriksaan awal paket, belum ada perubahan/push ke repository GitHub.

Revisi format 0.2: dokumentasi dan tabel dipindahkan ke Markdown. Nama zona diperjelas pada tabel subnet, daftar VM, dan interface router. Tidak ada uji engine atau uji lab tambahan.

Pemeriksaan revisi format: 13 baris VM memiliki nama zona; 8 subnet dan 10 interface router tercakup; 26 rencana rule dan 20 skenario uji dipertahankan. Tidak ada berkas CSV/TXT dalam paket. Referensi dokumen diperbarui; dua halaman PDF dirender ulang dan diperiksa secara visual.

## Revisi 0.3 - spesifikasi dan kapasitas

- Spesifikasi 13 VM dilengkapi dengan zona, OS/mode, vCPU, RAM, disk dan jumlah adapter: PASS (kelengkapan dokumen).
- Total alokasi dihitung dari 13 entri: 28 vCPU, 48 GiB RAM, 720 GiB disk virtual: PASS (aritmetika).
- Enam profil memakai 20, 23, 24, 23, 23 dan 24 GiB RAM VM; semuanya maksimal 24 GiB: PASS (aritmetika).
- Tabel CPU/RAM/disk pada IP/VLSM dicocokkan ke tabel spesifikasi: PASS (data statis).
- CPU/SSD aktual, pemakaian RAM host, startup, OOM, beban I/O, dan kinerja tiap profil: BELUM DIUJI.
- Alokasi gabungan SOC-IR 12 GiB masih perkiraan praktikum; bukan bukti seluruh dependency stabil.
- Tidak ada VM/hardware host, file sumber sinkronisasi, atau repository GitHub yang diubah.

## Revisi 0.4 - kondisi host dikonfirmasi pengguna

- CPU i9-10900K dan RAM 32 GB: dikonfirmasi pengguna; bukan pemeriksaan langsung host.
- Sisa ruang kosong sekitar 300 GB: dikonfirmasi pengguna; berbeda dari kapasitas total disk.
- Total target 720 GiB tetap kapasitas virtual seluruh VM; bukan permintaan ruang tambahan langsung di luar 300 GB.
- Panduan cadangan sekitar 50 GB dan pencatatan pertumbuhan disk ditambahkan; angka cadangan adalah usulan operasional, belum diuji.
- Pemakaian folder VM aktual, jenis disk, runtime disk, kinerja dan kecukupan retensi: BELUM DIUJI.

## Pemasukan sebagai draf repository

Pada 18 Oktober 2026, paket disiapkan pada folder `network-config/` di branch `feat/network-config` sesuai instruksi pengguna untuk push melalui SSH WSL. Pernyataan tidak ada perubahan repo pada pemeriksaan sebelumnya merujuk ke waktu paket awal disusun. README diperbarui untuk lokasi paket dan backlog audit; manifest dihitung ulang. Pengujian engine dan lab tetap BELUM DIUJI. Konfigurasi tim di `itcorner-id/` tidak diubah oleh pemasukan paket ini.

## Revisi 0.5 - dokumentasi target IPS

- Target akhir Suricata IPS ditulis pada README, panduan Edge/Internal, tabel peran, panduan SOC, spesifikasi dan topologi.
- Rencana IPS merinci kandidat Netmap/parent, baseline observasi, drop terpilih SID 1003001-1003004, SID 1003005/1003006 tetap alert, logging lokal/SOC, persistensi dan rollback.
- Lembar uji ditambah delapan skenario IPS-01 sampai IPS-08; semuanya BELUM DIUJI. Dua puluh skenario lama dipertahankan.
- Profil ketujuh P7 berisi VM 01/02/03/06/09/13 dengan total 22 GiB RAM dan 14 vCPU; belum ada benchmark.
- File rules, YAML, script dan PCAP tidak diubah; bug verifier negatif tetap backlog yang telah ditulis di README.
- Mode inline, parser engine, drop aktual, kompatibilitas driver/VLAN, performa, forwarding log dan uji lab: BELUM DIJALANKAN / BELUM DIUJI.

Pemeriksaan statis revisi IPS: 13 entri VM konsisten; 7 profil RAM maksimal 24 GiB termasuk P7 22 GiB/14 vCPU; 28 skenario tetap BELUM DIUJI; tautan relatif dan kolom tabel valid; hash seluruh 8 berkas rules/YAML/script/PCAP/fixture lain tidak berubah. Dua halaman topologi IPS dirender dan diperiksa secara visual. PASS untuk kelengkapan dokumen dan aritmetika; bukan pengujian IPS live.
