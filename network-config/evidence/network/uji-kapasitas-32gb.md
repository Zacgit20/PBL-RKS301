# Lembar uji kapasitas PC lab 32 GB

**Versi:** 0.5 - 18 Oktober 2026  
**Status semua pengukuran:** BELUM DIUJI  
**Acuan:** [spesifikasi dan profil VM](../../docs/network/spesifikasi-vm-32gb.md).

## Data host

| Item | Hasil aktual |
| --- | --- |
| Tanggal / penguji | Belum dicatat |
| Model CPU / core / logical processor | i9-10900K dikonfirmasi pengguna; jumlah core/logical processor yang terlihat host belum dicatat |
| RAM terpasang / usable | Pengguna menyebut 32 GB; usable belum dicatat |
| Versi Windows host / VMware Workstation | Belum dicatat |
| Jenis disk / kapasitas total | Belum dicatat |
| Sisa ruang kosong host | Sekitar 300 GB dikonfirmasi pengguna; pengukuran dan satuan aktual belum dicatat |
| Cadangan ruang kosong host | Usulan awal sekitar 50 GB; belum diuji |
| RAM available sebelum menyalakan VM | Belum dicatat |
| Folder lokasi VM / ukuran terpakai | Belum dicatat |

## Ringkasan per profil

Gunakan satu profil saja. Catat waktu startup, 5 menit idle dan minimal 15 menit beban ringan. Hasil tanpa pengukuran tidak boleh diberi PASS. Screenshot tidak perlu menampilkan password/token.

| Profil | VM aktif | Target RAM VM | vCPU | Status | RAM available host terendah | Catatan / lokasi bukti |
| --- | --- | --- | --- | --- | --- | --- |
| P1 - Jaringan dan domain | 01, 02, 08, 11, 12, 13 | 20 GiB | 12 | BELUM DIUJI | Belum dicatat | Belum ada |
| P2 - Aplikasi dan deploy | 01, 02, 03, 04, 05, 06, 08, 11 | 23 GiB | 15 | BELUM DIUJI | Belum dicatat | Belum ada |
| P3 - Monitoring Wazuh | 01, 02, 03, 06, 09, 11 | 24 GiB | 14 | BELUM DIUJI | Belum dicatat | Belum ada |
| P4 - Incident response | 01, 02, 04, 05, 10 | 23 GiB | 11 | BELUM DIUJI | Belum dicatat | Belum ada |
| P5 - Backup data | 01, 02, 05, 06, 07, 09, 12 | 23 GiB | 15 | BELUM DIUJI | Belum dicatat | Belum ada |
| P6 - API Wazuh ke SOC-IR | 02, 09, 10 | 24 GiB | 10 | BELUM DIUJI | Belum dicatat | Belum ada |
| P7 - Persiapan uji IPS | 01, 02, 03, 06, 09, 13 | 22 GiB | 14 | BELUM DIUJI | Belum dicatat | Belum ada |

## Catatan tiap pelaksanaan

Salin tabel ini untuk setiap profil dan setiap percobaan. Simpan bukti pada folder privat proyek sesuai akses tim. File hasil ukur dan penjelasan memakai Markdown.

| Data | Isian |
| --- | --- |
| Profil / nomor percobaan / tanggal | Belum dicatat |
| VM benar-benar aktif / RAM aktual VMware | Belum dicatat |
| Versi OS dan layanan utama | Belum dicatat |
| Mode Suricata / sensor / interface / ruleset / aksi efektif | Belum dicatat |
| Trafik normal dibanding beban uji IPS / drop atau error resource | Belum dicatat |
| Skenario / data / jumlah pengguna | Belum dicatat |
| Waktu mulai / durasi idle / durasi beban | Belum dicatat |
| RAM available host minimum selama uji | Belum dicatat |
| CPU host / guest dan kondisi disk | Belum dicatat |
| RAM guest / swap / kejadian OOM | Belum dicatat |
| Status service / container sebelum dan sesudah | Belum dicatat |
| Fungsi yang berhasil / gagal / waktu respons | Belum dicatat |
| Batas waktu respons yang disepakati | Belum dicatat |
| Lokasi screenshot / log hasil uji | Belum ada |
| Kesimpulan | BELUM DIUJI |
| Penyesuaian / tindak lanjut | Belum dicatat |

Kesimpulan boleh menjadi LULUS PROFIL hanya bila fungsi dalam profil berhasil, tidak ada OOM/restart karena RAM, host tidak macet akibat paging berkelanjutan, dan cadangan RAM available host memadai (target awal minimal 2 GiB saat beban). Bila gagal, catat PERLU PENYESUAIAN; revisi profil/alokasi kemudian ulangi uji. Lulus satu profil tidak berarti 12 VM atau seluruh integrasi live sudah berjalan bersamaan.

## Inventaris disk sebelum dan sesudah instalasi layanan

Isi ukuran terpakai folder VM saat guest shutdown untuk memperoleh titik awal yang konsisten. Catat pula runtime disk host saat profil menyala; berkas memory, snapshot dan suspend dapat mengubah pemakaian. Kolom target adalah kapasitas virtual rencana, bukan ruang tambahan yang harus dialokasikan ulang. Jangan menjumlahkan kapasitas virtual dengan ukuran berkas yang sama lalu menghitungnya dua kali.

| VM | Target disk virtual (GiB) | Ukuran folder aktual sebelum (GB/GiB, tulis satuan) | Sesudah layanan/data uji | Catatan snapshot / pertumbuhan |
| --- | --- | --- | --- | --- |
| VM-01 Edge OPNsense | 40 | Belum dicatat | Belum dicatat | Belum dicatat |
| VM-02 Internal OPNsense | 40 | Belum dicatat | Belum dicatat | Belum dicatat |
| VM-03 Web/App | 32 | Belum dicatat | Belum dicatat | Belum dicatat |
| VM-04 Management | 16 | Belum dicatat | Belum dicatat | Belum dicatat |
| VM-05 Management + Runner | 40 | Belum dicatat | Belum dicatat | Belum dicatat |
| VM-06 Database | 32 | Belum dicatat | Belum dicatat | Belum dicatat |
| VM-07 Backup | 64 | Belum dicatat | Belum dicatat | Belum dicatat |
| VM-08 Windows Server 2025 | 64 | Belum dicatat | Belum dicatat | Belum dicatat |
| VM-09 Wazuh | 80 | Belum dicatat | Belum dicatat | Belum dicatat |
| VM-10 SOC-IR | 160 | Belum dicatat | Belum dicatat | Belum dicatat |
| VM-11 Windows 11 Enterprise | 80 | Belum dicatat | Belum dicatat | Belum dicatat |
| VM-12 Ubuntu Client | 32 | Belum dicatat | Belum dicatat | Belum dicatat |
| VM-13 Kali Linux | 40 | Belum dicatat | Belum dicatat | Belum dicatat |

| Titik ukur | Ruang kosong host aktual | Tanggal / bukti |
| --- | --- | --- |
| Sebelum perubahan layanan | Perkiraan pengguna sekitar 300 GB; ukur lagi | Belum dicatat |
| Sesudah instalasi Wazuh dan SOC-IR | Belum dicatat | Belum dicatat |
| Saat profil terberat berjalan | Belum dicatat | Belum dicatat |
| Sesudah skenario dan backup | Belum dicatat | Belum dicatat |

Bandingkan pertumbuhan dengan sisa ruang host; pertahankan cadangan awal sekitar 50 GB dan evaluasi ulang bila pekerjaan memerlukan ruang lebih besar. Kecukupan storage belum diuji hanya dari konfirmasi angka 300 GB.

Target fitur Suricata adalah IPS. Anggaran P7 sebesar 22 GiB belum membuktikan kemampuan Netmap/driver atau performa ruleset; ukur CPU/RAM, I/O, packet drop akibat resource dan hasil fungsi. Bedakan drop karena policy keamanan dari packet loss karena resource. Bila perlu menambah RAM firewall, hitung ulang seluruh VM aktif terlebih dahulu. [Rencana IPS](../../docs/network/rencana-ips-opnsense.md).
