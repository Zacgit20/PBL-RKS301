# Matriks Aturan Firewall ITCorner.id

**Versi:** 1.0 (Revisi 3) - November 2026  
**Penanggung Jawab:** Muhammad Danish - System Integrator & Network Engineer  
**Status:** Baseline Arsitektur RPP Rev.3 (12 VM) & Penegakan ACL Least Privilege.

## Cara Membaca Matriks

Aturan dievaluasi pada antarmuka paket masuk (*ingress interface*), menerapkan prinsip *Default Deny* di mana semua trafik ditolak secara implisit kecuali dideklarasikan secara eksplisit. Trafik lintas dua firewall (Edge dan Internal) memerlukan deklarasi aturan dan rute yang selaras pada kedua sisi. Pengendalian trafik pada segmen VLAN yang sama (seperti Runner ke Windows DC pada VLAN 20, atau Database ke Backup pada VLAN 30) ditangani melalui firewall berbasis host (*Windows Firewall / UFW / iptables*).

| ID | Kontrol / Antarmuka Masuk | Sumber (Source) | Tujuan (Destination) | Protokol & Port | Aksi | Deskripsi & Kebutuhan Operasional |
| --- | --- | --- | --- | --- | --- | --- |
| E01 | Edge / WAN | Internet Publik | WAN IP -> Web/App 10.10.10.2 | TCP / 443 | DNAT + PASS | Akses e-commerce publik (HTTPS Nginx). Port 80 di-redirect ke 443. |
| E02 | Edge / WAN | Edge Local (Tailscale daemon) | Server Koordinasi & Relay Tailscale | UDP / 41641, TCP / 443 | PASS (Outbound) | Koneksi outbound control plane Tailscale. Tidak ada port inbound terbuka pada WAN. |
| E03 | Edge / Tailscale (`tailscale0`) | Admin Terotentikasi (100.64.0.0/10) | Web/App 10.10.10.2 | TCP / 443 | PASS | Akses dashboard `/admin` dengan allowlist IP Tailnet pada Nginx. |
| E04 | Edge + Internal / Tailscale Edge; Transit Internal | Admin Terotentikasi (100.64.0.0/10) | Management Server 10.10.20.2 | TCP / 22 | PASS | Akses administrasi SSH jarak jauh via Subnet Router. |
| D01 | Edge + Internal / DMZ Edge; Transit Internal | Web/App Server 10.10.10.2 | Database Server 10.10.30.2 | TCP / 5432 | PASS | Koneksi aplikasi Flask / SQLAlchemy ke basis data PostgreSQL. |
| D02 | Edge + Internal / DMZ Edge; Transit Internal | Web/App Server 10.10.10.2 | Wazuh SIEM 10.10.40.2 | TCP / 1514 | PASS | Pengiriman event dan alert agent Wazuh dari Web Server. |
| D03 | Edge + Internal / DMZ Edge; Transit Internal | Host terdaftar sementara | Wazuh SIEM 10.10.40.2 | TCP / 1515 | PASS | Pendaftaran / enrollment agent Wazuh baru (autentikasi kunci). |
| C01 | Internal + Edge / VLAN 50 Internal; Transit Edge | Client LAN (10.10.50.0/27) | Web/App Server 10.10.10.2 | TCP / 443 | PASS | Akses berbelanja pengguna internal ke web e-commerce ITCorner.id. |
| M01 | Internal + Edge / VLAN 20 Internal; Transit Edge | Management 10.10.20.2 | Web/App Server 10.10.10.2 | TCP / 22, 443 | PASS | Deployment pipeline CI/CD runner dan health check aplikasi. |
| M02 | Host Firewall / VLAN 20 (Local Host) | Management 10.10.20.2 | Windows Server 10.10.20.3 | TCP / 3389, 5986 | PASS (Host) | Remote administrasi Windows (RDP / WinRM) dari Management host. |
| M03 | Internal / VLAN 20 | Management 10.10.20.2 | Web GUI Firewall (10.10.1.1, 10.10.1.2) | TCP / 443 | PASS | Administrasi GUI OPNsense Edge dan Internal dari zona manajemen. |
| M04 | Internal + Edge / VLAN 20 Internal; Transit Edge | Runner 10.10.20.2 | GitHub API / Repositori / PyPI | TCP / 443 | PASS | Egress Runner CI/CD untuk fetch artefak dependensi & trigger pipeline. |
| A01 | Internal / VLAN 50 | Windows 11 (10.10.50.10), Ubuntu (10.10.50.20) | Windows Server 10.10.20.3 | TCP / 53, 88, 135, 389, 445, 464, 49152-65535 | PASS | Layanan Active Directory: Kerberos, RPC endpoint, LDAP, SMB file share. |
| A02 | Internal / VLAN 50 | Windows 11 (10.10.50.10), Ubuntu (10.10.50.20) | Windows Server 10.10.20.3 | UDP / 53, 88, 123, 389, 464 | PASS | Layanan DNS query, Kerberos auth, NTP waktu domain internal. |
| L01 | Internal / VLAN 20, 30, 50, 60 | Seluruh Wazuh Agent terpasang | Wazuh SIEM 10.10.40.2 | TCP / 1514 | PASS | Pengiriman telemetri, log audit, dan security events ke SIEM Manager. |
| L02 | Internal / VLAN 20, 30, 50, 60 | Agent belum terdaftar | Wazuh SIEM 10.10.40.2 | TCP / 1515 | PASS | Port registrasi agent Wazuh (authd). |
| L03 | Edge + Internal / Firewall Transit | OPNsense Edge & Internal | Wazuh SIEM 10.10.40.2 | UDP / 514 | PASS | Pengiriman syslog filterlog OPNsense (firewall events) ke SIEM. |
| L04 | Internal + Edge / VLAN 40 Internal; Transit Edge | Wazuh SIEM 10.10.40.2 | Telegram Bot API (`api.telegram.org`) | TCP / 443 | PASS | Notifikasi otomatis alert Wazuh Level >= 10 ke grup Telegram SOC. |
| N01 | Internal + Edge / Egress Semua Zona | Seluruh Host & Firewall | Upstream NTP Server / Pool | UDP / 123 | PASS | Sinkronisasi waktu sistem (presisi offset < 0.03s untuk korelasi forensik). |
| T01 | Internal + Edge / VLAN 60 Internal; Transit Edge | Kali Linux 10.10.60.2 | Web/App Server 10.10.10.2 | TCP / 80, 443 | PASS (Jadwal) | Simulasi serangan web & port scan terkontrol (dengan izin/tiket teruji). |
| B01 | Internal / VLAN 60 | Kali Linux 10.10.60.2 | VLAN 20, 30, 40, 50 | Any / Any | BLOCK + LOG | Isolasi ketat host penyerang; dilarang mengakses zona internal lain. |
| B02 | Internal / VLAN 50 | Client LAN 10.10.50.0/27 | DB (10.10.30.2), Backup, SOC Zone | Any / Any | BLOCK + LOG | Pelanggan dan staf umum dilarang langsung menyentuh basis data / SOC. |
| B03 | Edge / WAN | Internet Publik | Seluruh Segmen Internal & Manajemen | Any / Any | BLOCK + LOG | Penolakan *Default Deny* terhadap seluruh koneksi tak diizinkan dari luar. |
| H01 | Host Firewall / VLAN 30 (Local Host) | Database Server 10.10.30.2 | Backup Server 10.10.30.3 | TCP / 22 (SFTP) | PASS (Host) | Replikasi pencadangan otomatis terenkripsi Restic mode *append-only*. |

## Catatan Teknis & Penegakan Keamanan

1. **Penggantian WireGuard dengan Tailscale:**
   * Tidak ada port WAN inbound yang dibuka untuk VPN (aturan lama E02 dihapus). Edge OPNsense menjalankan Tailscale dalam mode Subnet Router (`--advertise-routes=10.10.10.0/29,10.10.20.0/29 --snat-subnet-routes=false`).
   * Internal OPNsense memiliki rute statis: `100.64.0.0/10` via `10.10.1.1` (Edge Transit) sehingga alur kembali (*return path*) tidak terputus.
2. **Ketiadaan Bastion Terpisah:**
   * Fungsi Bastion VM digantikan oleh perpaduan Tailscale ACL, MFA pada identity provider, dan akses terarah ke Management Server (`10.10.20.2`).
3. **Pemisahan Trafik Windows DC (VLAN 20):**
   * Windows DC kini berada pada VLAN 20 (`10.10.20.3`). Akses dari Client (VLAN 50) hanya diizinkan untuk port esensial domain (DNS, Kerberos, LDAP, SMB, RPC). Akses administratif RDP dibatasi hanya dari host Management (`10.10.20.2`) melalui Windows Firewall.
4. **Pencegahan Bypass pada Kali Linux (VLAN 60):**
   * Kali Linux (`10.10.60.2/29`) dibatasi penuh oleh aturan `B01`. Akses uji ke Web Server (`T01`) hanya diaktifkan selama simulasi pengujian penetrasi terjadwal.

## Integrasi dengan Suricata NIDS/IPS

Aturan firewall di atas bertindak sebagai lapisan penyaring paket (*Packet Filter Layer 3/4*). Trafik yang diizinkan (PASS) pada tabel di atas tetap diinspeksi secara *inline* oleh engine Suricata pada router OPNsense:
* **SID 1000001:** Memantau lonjakan SYN scan dari Kali ke Web Server.
* **SID 1000002:** Memantau percobaan brute-force SSH ke Web Server.
* **SID 1000003:** Memblokir langsung percobaan akses ilegal ke port 5432 PostgreSQL yang tidak bersumber dari Web Server `10.10.10.2`.
* **SID 1000004:** Mendeteksi percobaan injeksi SQL (`UNION SELECT`) pada lalu lintas HTTP.
