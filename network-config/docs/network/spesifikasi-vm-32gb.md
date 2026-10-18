# Spesifikasi 13 VM dan rencana pemakaian PC lab 32 GB

**Versi:** 0.4 - 18 Oktober 2026  
**Penanggung jawab:** Muhammad Danish - PM & Network Engineer  
**Status:** usulan alokasi untuk praktikum; belum diukur pada PC lab.

## 1. Keputusan kapasitas

PC lab RAM 32 GB direncanakan dipakai dengan **VM menyala bergantian sesuai profil**, maksimal 24 GiB RAM VM aktif. Seluruh 13 VM tetap menjadi bagian topologi dan tetap terpasang. Tabel di bawah membutuhkan total 48 GiB bila semuanya dinyalakan, sehingga **13 VM dengan seluruh layanan tersebut tidak direncanakan aktif bersamaan pada satu PC 32 GB**.

Anggaran awal menyisakan sekitar 8 GiB untuk Windows host, VMware, dan ruang cadangan. Ini bukan jaminan kinerja: jumlah RAM usable, pemakaian Windows, CPU, SSD, versi layanan, dan beban nyata harus dicek di lab. Bila host memerlukan lebih banyak RAM, kurangi VM aktif dari profil; jangan menurunkan komponen penting di bawah kebutuhannya agar angka terlihat muat.

RAM dan disk tabel memakai **GiB** (1 GiB = 1024 MiB). Label 32 GB mengikuti penyebutan PC pengguna; catat RAM usable yang ditampilkan Windows. Angka disk adalah kapasitas virtual target, bukan seluruhnya langsung terpakai di disk host.

## 2. Spesifikasi tiap VM

Angka berikut adalah target awal untuk lab ringan, bukan hasil membaca setting VM yang sudah terpasang. Tetap gunakan instalasi yang sudah ada bila kompatibel. Versi OS Linux aktual perlu dicatat; untuk instalasi baru pilih versi LTS yang didukung versi aplikasi, misalnya Ubuntu Server 24.04 LTS pada stack yang mendukungnya.

| No. VM | Nama VM | Nama zona | OS / mode | vCPU total | RAM (GiB) | Disk virtual (GiB) | Jumlah vNIC | Penggunaan / batas |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 01 | Edge OPNsense | Perimeter / Transit / DMZ | OPNsense amd64 | 2 | 4 | 40 | 3 | WAN, Transit, trunk DMZ; WireGuard interface virtual |
| 02 | Internal OPNsense | Transit / gateway VLAN internal | OPNsense amd64 | 2 | 4 | 40 | 2 | Transit dan trunk VLAN 20/30/40/50/60 |
| 03 | Web/App | DMZ | Linux Server LTS tanpa desktop | 2 | 2 | 32 | 1 | Nginx + ModSecurity/CRS + Flask/Gunicorn dalam Docker |
| 04 | Bastion | DMZ | Linux Server LTS tanpa desktop | 1 | 1 | 16 | 1 | SSH jump host; tanpa aplikasi tambahan |
| 05 | Management + Runner | DevOps & Management | Ubuntu Server LTS tanpa desktop | 2 | 2 | 40 | 1 | Administrasi CLI; satu job runner pada satu waktu |
| 06 | Database | Server/Data | Linux Server LTS tanpa desktop | 2 | 2 | 32 | 1 | PostgreSQL; dataset kecil untuk praktikum |
| 07 | Backup | Server/Data | Linux Server LTS tanpa desktop | 1 | 1 | 64 | 1 | Restic/SSH/SFTP; backup data terpilih, bukan image semua VM |
| 08 | Windows Server 2025 | Server/Data | Windows Server 2025 | 2 | 4 | 64 | 1 | AD DS + DNS untuk domain lab kecil |
| 09 | Wazuh | SOC | Ubuntu Server LTS yang didukung Wazuh | 4 | 8 | 80 | 1 | Manager + Indexer + Dashboard; bukan hanya agent |
| 10 | SOC-IR | SOC | Ubuntu Server LTS yang didukung stack | 4 | 12 | 160 | 1 | TheHive + Cortex + MISP beserta dependency; anggaran uji terbatas |
| 11 | Windows 11 Enterprise | Internal Client | Windows 11 Enterprise | 2 | 4 | 80 | 1 | Client domain; UEFI, Secure Boot capable, vTPM 2.0 |
| 12 | Ubuntu Client | Internal Client | Ubuntu dalam mode terminal | 2 | 2 | 32 | 1 | Client CLI; alokasi ini tidak ditujukan ke desktop penuh |
| 13 | Kali Linux | Security Testing | Kali Linux; tools seperlunya | 2 | 2 | 40 | 1 | Satu pengujian kecil pada satu waktu; tanpa pemindaian massal |

**Total seluruh 13 VM:** 28 vCPU terkonfigurasi, 48 GiB RAM, 720 GiB kapasitas disk virtual. vCPU dibagi waktu oleh hypervisor, bukan core fisik yang dipasang terpisah untuk setiap VM. Tidak ada kebutuhan GPU khusus pada peran dalam tabel.

WireGuard adalah layanan pada Edge, sehingga tidak ditambah sebagai VM ke-14. SOC-IR tetap satu VM; RAM-nya mencakup seluruh container dan dependency di dalamnya. Tabel IP, nama zona, VLAN, dan gateway tersedia di [tabel IP/VLSM](tabel-ip-vlsm.md).

## 3. Dasar alokasi komponen berat

- **OPNsense: 4 GiB per VM.** Ini mengikuti kelas reasonable 4 GB/SSD 40 GB pada dokumentasi untuk fitur standar dengan beban ringan. Rules IDS/IPS dan volume trafik menambah beban; alokasi tersebut bukan janji throughput atau kemampuan menjalankan semua rules. Mulai dengan rules yang diperlukan, lalu ukur. [OPNsense hardware sizing](https://docs.opnsense.org/manual/hardware.html).
- **Wazuh: 4 vCPU dan 8 GiB.** Acuan quickstart all-in-one untuk 1-25 agent menyebut 4 vCPU, 8 GiB dan storage 50 GB. Disk 80 GiB adalah usulan lab dengan ruang OS/log tambahan; retensi 90 hari tidak otomatis terjamin. [Wazuh quickstart](https://documentation.wazuh.com/current/quickstart.html).
- **SOC-IR: 12 GiB adalah perkiraan praktikum gabungan, bukan minimum resmi seluruh stack.** StrangeBee memberi profil Docker Compose testing TheHive+Cortex beserta dependency pada 8 GB/4 vCPU; MISP menyebut penggunaan kecil dapat berjalan pada 4 GB. Penjumlahan itu menjadi titik awal 12 GiB, tetapi OS bersama, analyzer, worker, database dan indeks tetap harus diukur. Batasi pada satu pengguna dan data kecil. Jika tidak cukup, tambah RAM VM dan hitung ulang profil atau jalankan layanan SOC-IR bergantian. [TheHive requirements](https://docs.strangebee.com/thehive/installation/system-requirements/), [MISP performance tuning](https://www.misp-project.org/misp-performance-tuning/).
- **Windows 11: 4 GiB, 2 vCPU, disk 80 GiB.** Ini anggaran awal; Windows sendiri mensyaratkan RAM 4 GB, storage 64 GB, CPU kompatibel dengan minimal dua core, UEFI/Secure Boot capable dan TPM 2.0. Pertahankan vTPM dan konfigurasi Windows yang didukung. [Windows 11 specifications](https://www.microsoft.com/en-us/windows/windows-11-specifications).
- **Windows Server 2025: 4 GiB/2 vCPU/disk 64 GiB** diusulkan untuk AD/DNS lab kecil; ukur lagi setelah domain dan agent aktif. Persyaratan OS bukan jaminan kapasitas untuk semua role. [Windows Server requirements](https://learn.microsoft.com/en-us/windows-server/get-started/hardware-requirements).
- **VM Linux kecil:** anggaran pada tabel berlaku untuk mode terminal, dataset kecil, dan sedikit koneksi. Ubuntu Client 2 GiB dipakai sebagai client CLI. Jika Ubuntu Client yang terpasang memakai desktop penuh dan membutuhkan 4 GiB, profil P1 menjadi 22 GiB; P5 menjadi 25 GiB dan harus dikurangi, misalnya mematikan Management/Runner sehingga kembali 23 GiB. GUI Management juga memerlukan hitungan baru.

## 4. Profil VM yang dinyalakan

**Pilih satu profil pada satu waktu. Semua VM yang tidak tercantum harus shutdown**, termasuk VM dari profil sebelumnya. Jangan menambahkan VM ke profil tanpa menghitung RAM ulang. Nomor di tabel merujuk ke daftar 13 VM di atas.

| Profil | VM aktif (nomor) | Jumlah VM | RAM VM (GiB) | vCPU aktif | Ruang nominal host dari 32 GiB | Tujuan dan batas |
| --- | --- | --- | --- | --- | --- | --- |
| P1 - Jaringan dan domain | 01, 02, 08, 11, 12, 13 | 6 | 20 | 12 | 12 GiB | VLAN, routing, AD/DNS dan client; layanan Web/DB/SOC belum aktif. |
| P2 - Aplikasi dan deploy | 01, 02, 03, 04, 05, 06, 08, 11 | 8 | 23 | 15 | 9 GiB | Web/WAF, DB, domain, Bastion dan runner; Wazuh/SOC-IR belum aktif. |
| P3 - Monitoring Wazuh | 01, 02, 03, 06, 09, 11 | 6 | 24 | 14 | 8 GiB | Log Web/WAF ke Wazuh dan request uji dari Windows; AD/DNS dan SOC-IR mati. |
| P4 - Incident response | 01, 02, 04, 05, 10 | 5 | 23 | 11 | 9 GiB | TheHive/Cortex/MISP, administrasi dan egress; Wazuh serta aplikasi mati. |
| P5 - Backup data | 01, 02, 05, 06, 07, 09, 12 | 7 | 23 | 15 | 9 GiB | Backup/restore data DB dan data SOC terpilih; AD/DNS dan Web mati. |
| P6 - API Wazuh ke SOC-IR | 02, 09, 10 | 3 | 24 | 10 | 8 GiB | Integrasi lokal di VLAN 40 dengan data tersimpan; Edge, Internet, client dan aplikasi mati. |

Urutan umum menyalakan VM: Edge jika ada dalam profil, Internal, server yang dibutuhkan, lalu client/runner. Nyalakan satu per satu dan tunggu layanan siap; jangan boot seluruhnya bersamaan. Shutdown guest dengan normal setelah sesi selesai. Profil P6 hanya menyalakan Internal, Wazuh dan SOC-IR.

### Ketergantungan yang perlu diperhatikan

- P1 menguji jaringan/domain; P2 menguji aplikasi. P2 belum membuktikan log sampai ke Wazuh atau case terbentuk di TheHive.
- P3 tidak menyalakan Windows Server. Pengujian Web/DB lokal dapat menggunakan IP atau entri hosts khusus lab dengan Host/SNI yang sesuai. Login domain, DNS AD, dan autentikasi LDAP yang memerlukan server tersebut tidak tercakup. Jangan mencatat keberhasilan fitur domain saat DC mati.
- P3 memakai Windows 11 untuk request aplikasi. Akses administrator ke dashboard SOC tetap mengikuti matriks firewall; profil ini tidak mengizinkan client VLAN 50 mengelola SOC secara otomatis. Bila perlu browser admin, sesuaikan komposisi profil dan rute yang diizinkan terlebih dahulu.
- P4 menggunakan log/alert yang sudah disimpan atau data uji yang diberi label. Wazuh dan Web mati, sehingga tidak membuktikan alur serangan langsung dari aplikasi sampai SOC-IR. Analyzer yang memerlukan Internet hanya diuji jika egress sudah dikonfigurasi dan diizinkan.
- P5 menargetkan data aplikasi/DB dan data SOC terpilih sesuai kapasitas backup. Ini bukan backup image seluruh 13 VM. AD mati; gunakan akses uji lokal yang diizinkan atau IP bila sesuai skenario. Prosedur backup konsisten dan uji restore tetap diperlukan.
- P6 menyalakan Wazuh dan SOC-IR pada subnet/VLAN 40 yang sama. Pengujian API dapat dimulai dari console VM; tagging LAN Segment dan konektivitas lokal tetap perlu dibuktikan. Edge mati, maka Telegram, feed eksternal, analyzer online, dan akses Internet tidak termasuk. Tidak ada VM browser/admin tambahan pada anggaran ini.
- Host Windows tidak otomatis bisa mengakses LAN Segment. Jangan menganggap browser host dapat membuka dashboard hanya karena VM menyala; ikuti akses management yang sudah dirancang.

Profil ini membantu menyelesaikan dan mendemonstrasikan bagian proyek secara bertahap. Jika manajer proyek meminta **13 VM dan seluruh alur live aktif serentak**, kebutuhan itu memerlukan pembagian ke host lain atau penambahan RAM. Berdasarkan anggaran 48 GiB VM + sekitar 8 GiB host = 56 GiB, **64 GB merupakan kandidat kapasitas host**, lalu tetap diuji dengan beban nyata; kebutuhan dapat naik jika SOC-IR membesar. Penggunaan beberapa host juga memerlukan desain jaringan antar-host, karena LAN Segment lokal tidak otomatis menjangkau PC lain.

## 5. CPU dan storage host

**CPU i9-10900K sudah dikonfirmasi pengguna pada 18 Oktober 2026. RAM terpasang 32 GB dan sisa ruang kosong disk sekitar 300 GB juga dikonfirmasi pengguna.** Angka 300 GB adalah ruang kosong, bukan kapasitas total disk. Jenis disk dan pemakaian folder VM saat ini belum dicatat. Periksa virtualisasi aktif dan RAM usable di Task Manager. Mulai dari vCPU pada tabel dan hindari menambah core untuk semua VM sekaligus. VM 2 vCPU bisa diatur sebagai satu processor dengan dua core; yang diperhitungkan adalah jumlah vCPU total.

Disk target seluruh VM berjumlah **720 GiB secara logis**. Dengan disk growable/thin, ukuran berkas awal di host dapat lebih kecil dan bertambah saat terisi. **720 GiB bukan permintaan ruang tambahan di luar 300 GB kosong**: 13 VM telah terpasang dan berkasnya sudah menggunakan sebagian kapasitas disk. Ukuran folder VM aktual, kapasitas virtual yang sudah dialokasikan, dan pertumbuhan data perlu diperiksa sebelum menyimpulkan cukup atau kurang.

Sebagai perencanaan batas pertumbuhan saat seluruh virtual disk mendekati penuh, anggaran folder lab sekitar **800 GiB di luar ruang Windows host** (bukan syarat ruang tambahan saat ini): 720 GiB disk virtual, hingga sekitar 24 GiB berkas backing memory pada profil, dan cadangan kerja terbatas. Snapshot, suspend, salinan image, ISO, pertumbuhan log dan backup tambahan dapat melampaui anggaran itu. Ukuran snapshot tidak dibatasi oleh cadangan tersebut; hitung sesuai perubahan nyata. PC dengan SSD berlabel 1 TB belum tentu memiliki sisa ruang yang cukup setelah Windows dan aplikasi.

Gunakan SSD untuk VM Wazuh dan SOC-IR; I/O disk dapat menjadi bottleneck walaupun RAM masih tersedia. **Ruang kosong sekitar 300 GB sudah dikonfirmasi; jenis dan kapasitas total disk belum dicatat.** Jangan memperkecil disk VM yang sudah terpasang hanya untuk menyesuaikan tabel. Bila ruang kurang, tinjau pemakaian aktual dan disk data terpisah bersama tim sebelum perubahan.

### Pemakaian sisa ruang sekitar 300 GB

- Lanjutkan dari 13 VM yang sudah terpasang; tidak perlu membuat ulang atau menggandakan image. Mematikan VM menghemat RAM, tetapi tidak menghapus pemakaian disk VM tersebut.
- Gunakan 300 GB sebagai **batas ruang tambahan yang masih tersedia**, bukan anggaran baru yang diberikan ke tiap VM. Sebagai batas kerja awal, pertahankan setidaknya sekitar **50 GB tetap kosong di host** untuk berkas runtime VMware, pertumbuhan Windows dan ruang kerja. Artinya sekitar 250 GB menjadi batas kasar pertumbuhan tambahan dari kondisi sekarang, bukan target untuk dihabiskan. Angka cadangan ini usulan operasional, bukan syarat resmi VMware; tambah cadangan bila ada snapshot/suspend, pembaruan atau beban lebih besar. Bila 300 GB ternyata dibaca sebagai GiB oleh Windows, catat satuan aslinya saat mengukur.
- Mulai dengan dataset praktikum kecil. Catat pertumbuhan disk setelah memasang Wazuh dan dependency SOC-IR, menarik container image, menambah log, feed MISP atau menjalankan build. Jangan mengimpor seluruh feed atau menyimpan log tanpa batas. Retensi disepakati tim; simpan evidence yang diperlukan sebelum penghapusan yang disetujui.
- Backup 64 GiB pada tabel adalah kapasitas virtual target untuk data terpilih, bukan cadangan penuh 13 VM. Backup di disk fisik yang sama tetap memakai ruang host dan tidak melindungi dari kerusakan disk host. Lokasi salinan terpisah dicatat bila tersedia.
- Jangan menghapus snapshot atau file VM secara manual untuk mengejar ruang. Inventarisasi terlebih dahulu dan lakukan perubahan melalui prosedur VMware/tim yang sesuai. Paket ini tidak mengubah disk atau VM lab.
- Jika ruang kosong mendekati cadangan, hentikan dulu penambahan feed, build atau pekerjaan penghasil data besar dan tinjau pertumbuhannya. Bila kebutuhan proyek melampaui sisa ruang, gunakan storage tambahan yang tersedia atau pindahkan VM/data melalui rencana tim; jangan menyatakan seluruh alokasi 720 GiB dijamin muat dalam sisa 300 GB.

Dengan kondisi ini, **penggunaan RAM bergantian tetap menjadi rencana utama; kecukupan disk dinilai dari ukuran nyata dan pertumbuhan data**. Sisa 300 GB belum menjadi alasan untuk menyatakan pasti kekurangan disk, tetapi juga belum membuktikan seluruh stack dan retensinya akan muat. Inventaris dan pengukuran dicatat pada lembar uji kapasitas.

## 6. Pengaturan operasional VMware

1. Saat VM sudah shutdown, cocokkan CPU/RAM dengan tabel. Perubahan hardware dilakukan di lab; dokumen ini tidak mengubah VM secara otomatis.
2. Pastikan versi Workstation mendukung guest OS yang dipakai. Pertahankan VMware Tools/open-vm-tools yang sesuai; jangan mengganti jenis NIC atau nama interface firewall tanpa memetakan MAC terlebih dahulu.
3. Pertahankan jumlah adapter dan koneksi jaringan yang direncanakan: Edge 3 adapter, Internal 2 adapter, host lain masing-masing 1. Subinterface VLAN tidak membutuhkan vNIC baru. Mapping Edge masih perlu diverifikasi; Internal em0 Transit dan em1 trunk mengikuti bukti sebelumnya.
4. Sebelum menjalankan profil, tutup aplikasi host berat yang tidak diperlukan. Periksa RAM available dan pemakaian disk; jika host sudah memakai lebih dari anggaran 8 GiB, kurangi RAM VM aktif dengan mematikan VM yang tidak diperlukan, bukan memaksa host paging.
5. Hindari menjalankan build Docker, pembaruan OS besar, impor feed MISP, analyzer berat, dan scan Kali secara bersamaan. Jalankan job satu per satu. Jangan mematikan kontrol keamanan Windows/firewall untuk menghemat resource.
6. Pada SOC-IR, konfigurasi heap JVM dan worker sesuai versi container; periksa total seluruh dependency. Jangan menjadikan swap/pagefile sebagai tambahan RAM untuk mengklaim semua VM muat. Retensi log disepakati tim dan bukti uji penting diekspor sebelum penghapusan yang disetujui.

## 7. Cara menyatakan sudah mampu berjalan

Angka anggaran profil sudah diperiksa secara hitungan. **Kinerja dan keberhasilan menjalankan stack belum diuji di PC lab**, sehingga status saat ini adalah LAYAK DICOBA BERTAHAP, bukan LULUS UJI 32 GB.

Untuk setiap profil yang diperlukan: catat host dan versi aplikasi, nyalakan VM sesuai daftar, tunggu startup selesai, amati idle sekitar 5 menit, lalu jalankan skenario ringan selama sedikitnya 15 menit. Nilai waktu ini adalah prosedur praktikum usulan, bukan benchmark resmi. Catat RAM host available, RAM/CPU guest, aktivitas disk, status container/service dan hasil fungsi yang diuji.

Kriteria awal penerimaan: tidak ada OOM atau restart service karena RAM; tidak ada paging host yang terus membebani disk dan membuat VM macet; masih ada RAM available host (target cadangan minimal 2 GiB selama beban); layanan yang diperlukan siap; dan transaksi/uji profil berhasil dengan waktu respons yang disepakati tim. Jika gagal, tandai PERLU PENYESUAIAN dan revisi komposisi/alokasi lalu ulangi. Jangan menyebut seluruh integrasi live lulus berdasarkan pengujian komponen bergantian.

Catat hasil di [lembar uji kapasitas](../../evidence/network/uji-kapasitas-32gb.md). Sumber teknis dan keputusan terbuka dirangkum di [REFERENSI.md](REFERENSI.md).
