# Matriks aturan firewall ITCorner.id

Versi 0.2 - 18 Oktober 2026. Seluruh baris adalah rencana akses; bukan file konfigurasi yang bisa diimpor langsung. Terapkan setelah memeriksa pemetaan interface dan akses pemulihan console.

## Cara membaca

Aturan dievaluasi pada interface masuk, dengan exception yang spesifik sebelum penolakan umum. Trafik yang melewati dua firewall perlu rule dan route yang sesuai pada keduanya. Kontrol sesama subnet seperti Bastion ke Web/App atau Database ke Backup dipasang pada host/kontrol lokal karena tidak otomatis melewati router.

| ID | Kontrol / interface masuk | Sumber | Tujuan | Layanan | Aksi target | Kapan aktif / status |
| --- | --- | --- | --- | --- | --- | --- |
| E01 | Edge / WAN | Internet | WAN address -> Web/App 10.10.10.2 | TCP / 443 | DNAT + PASS | Saat HTTPS siap / RENCANA |
| E02 | Edge / WAN | Peer admin terdaftar | WAN address | UDP / 51820 | PASS | Saat WireGuard siap / RENCANA |
| E03 | Edge / WireGuard | Peer admin terdaftar | Bastion 10.10.10.3 | TCP / 22 | PASS | Administrasi / RENCANA |
| E04 | Edge + Internal / WireGuard Edge; Transit Internal | Peer admin terdaftar | Management 10.10.20.2 | TCP / 22;443 | PASS | Administrasi / RENCANA |
| D01 | Edge + Internal / DMZ Edge; Transit Internal | Web/App 10.10.10.2 | DB 10.10.30.2 | TCP / 5432 | PASS | Layanan aplikasi / RENCANA |
| D02 | Edge + Internal / DMZ Edge; Transit Internal | Web/App; Bastion | Wazuh 10.10.40.2 | TCP / 1514 | PASS | Agent siap / RENCANA |
| D03 | Edge + Internal / DMZ Edge; Transit Internal | Agent terdaftar | Wazuh 10.10.40.2 | TCP / 1515 | PASS | Enrollment sementara / RENCANA |
| C01 | Internal + Edge / VLAN50 Internal; Transit Edge | Client VLAN50 | Web/App 10.10.10.2 | TCP / 443 | PASS | Layanan aplikasi / RENCANA |
| M01 | Internal + Edge / VLAN20 Internal; Transit Edge | Management 10.10.20.2 | Web/App 10.10.10.2 | TCP / 22;443 | PASS | Deployment/health check / RENCANA |
| M02 | Internal / VLAN20 | Management 10.10.20.2 | DC 10.10.30.4 | TCP / 3389;5986 | PASS | Administrasi Windows / RENCANA |
| M03 | Internal / VLAN20 | Management 10.10.20.2 | Alamat pengelolaan firewall | TCP / 443 | PASS | Administrasi / RENCANA |
| M04 | Internal + Edge / VLAN20 Internal; Transit Edge | Runner 10.10.20.2 | Alias GitHub/GHCR/dependency disetujui | TCP / 443 | PASS | CI/CD / RENCANA |
| A01 | Internal / VLAN50 | Windows11 10.10.50.10; Ubuntu10.10.50.20 | DC 10.10.30.4 | TCP / 53;88;135;389;445;464;49152-65535 | PASS | AD siap / RENCANA |
| A02 | Internal / VLAN50 | Windows11 10.10.50.10; Ubuntu10.10.50.20 | DC 10.10.30.4 | UDP / 53;88;123;389;464 | PASS | AD siap / RENCANA |
| L01 | Internal / VLAN20/30/50/60 | Agent yang disetujui | Wazuh 10.10.40.2 | TCP / 1514 | PASS | Agent siap / RENCANA |
| L02 | Internal / VLAN20/30/50/60 | Agent yang didaftarkan | Wazuh 10.10.40.2 | TCP / 1515 | PASS | Enrollment sementara / RENCANA |
| L03 | Edge + Internal / Keluar firewall; Transit sesuai jalur | IP firewall pengirim | Wazuh/collector 10.10.40.2 | UDP / 514 | PASS | Collector disepakati / RENCANA |
| L04 | Internal + Edge / VLAN40 Internal; Transit Edge | Wazuh 10.10.40.2 | Alias Telegram API | TCP / 443 | PASS | Notifikasi siap / RENCANA |
| N01 | Internal + Edge / Interface asal sesuai zona | Host yang disetujui | Resolver/NTP yang disepakati | Sesuai layanan / 53;123 sesuai keputusan | PASS | Setelah target ditentukan / BUTUH PARAMETER |
| T01 | Internal + Edge / VLAN60 Internal; Transit Edge | Kali 10.10.60.2 | Web/App 10.10.10.2 | TCP / 8080 | PASS | Jendela uji HTTP terisolasi / RENCANA SEMENTARA |
| T02 | Internal + Edge / VLAN60 Internal; Transit Edge | Kali 10.10.60.2 | Bastion 10.10.10.3 | TCP / 22 | PASS | Jendela uji disetujui / RENCANA SEMENTARA |
| B01 | Internal / VLAN60 | Kali 10.10.60.2 | Jaringan proyek lainnya | Any / Any | BLOCK + LOG | Selain exception uji / RENCANA |
| B02 | Internal / VLAN50 | Client VLAN50 | DB 10.10.30.2; Backup10.10.30.3; SOC10.10.40.0/29 | Any / Any | BLOCK + LOG | Operasional / RENCANA |
| B03 | Edge / WAN | Internet | Jaringan internal dan admin | Any / Any | BLOCK | Default / RENCANA |
| H01 | Firewall host / DMZ sesama subnet | Bastion 10.10.10.3 | Web/App10.10.10.2 | TCP / 22 | PASS terbatas | Administrasi / RENCANA |
| H02 | Firewall host / Server sesama subnet | Database10.10.30.2 | Backup10.10.30.3 | TCP / 22 / port Restic yang dipilih | PASS terbatas | Backup terjadwal / BUTUH PARAMETER |

## Catatan setiap aturan

- **E01:** Filter terkait DNAT; tidak membuka SSH/DB/RDP.
- **E02:** Kunci dan peer tidak termasuk paket.
- **E03:** Tidak membuka SSH dari WAN langsung.
- **E04:** Route tunnel balik dan AllowedIPs harus sesuai.
- **D01:** Pertahankan source; PostgreSQL juga membatasi host/user.
- **D02:** Cocokkan port/protokol agent aktual.
- **D03:** Cabut/batasi setelah enrollment sesuai prosedur.
- **C01:** Akses via alamat DNS lab yang benar.
- **M01:** SSH runner exception terpisah dari jalur admin manual Bastion.
- **M02:** WinRM HTTPS; 5985 hanya bila disetujui terpisah.
- **M03:** Tujuan alias admin spesifik; jaga console pemulihan.
- **M04:** Domain/IP CDN berubah; kelola alias tujuan sesuai kebutuhan.
- **A01:** Dynamic RPC dibatasi sumber dan tujuan; LDAP secure/GC opsional ditinjau.
- **A02:** Sesuaikan kebutuhan integrasi Ubuntu.
- **L01:** Per VLAN; tidak mengizinkan seluruh layanan SOC.
- **L02:** Batasi masa aktif.
- **L03:** Contoh syslog; ganti ke transport TLS bila collector mendukung; jangan buka dua-duanya tanpa kebutuhan.
- **L04:** Token dikelola privat; uji notifikasi bersama SOC.
- **N01:** Pisahkan DNS TCP/UDP dan NTP UDP; bukan rule any.
- **T01:** Bukan layanan publik; tutup setelah uji; parser HTTP harus melihat request.
- **T02:** Untuk uji koneksi; kegagalan auth dari log host.
- **B01:** Setelah allow spesifik; tidak ada akses permanen menyeluruh.
- **B02:** Tempatkan setelah exception yang disetujui; tidak mengubah akses DC.
- **B03:** Exception hanya layanan publik dan tunnel yang disepakati.
- **H01:** Tidak melewati router; perlu kontrol host/akses SSH.
- **H02:** Tidak melewati router; definisikan push/pull dan transport.

## Pemeriksaan sebelum penerapan

Pastikan target DNS/NTP, listener log, port backup, peer VPN, dan alias egress yang belum diketahui sudah diisi dengan nilai nyata. Rule sementara Kali dicabut setelah pengujian. Periksa NAT agar source IP antar-zona tidak berubah tanpa sengaja. Status RENCANA pada dokumen ini tidak sama dengan rule yang sudah aktif atau lulus uji.
