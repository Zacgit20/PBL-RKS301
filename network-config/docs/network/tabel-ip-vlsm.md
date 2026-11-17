# Tabel IP dan VLSM ITCorner.id

**Versi:** 1.0 (Revisi 3) - November 2026  
**Status:** Baseline Arsitektur RPP Rev.3 (12 VM) & Evaluasi ATS.

Nama zona dicantumkan pada pembagian subnet, daftar host, dan daftar interface. Alamat yang sudah terpasang di lab disesuaikan dengan arsitektur 12 VM terbaru tanpa Bastion Host terpisah, integrasi Tailscale Subnet Router pada Edge OPNsense, serta migrasi Windows Server (AD DS/DNS) ke VLAN 20 Management.

## 1. Pembagian zona, VLAN, dan gateway

| Nama zona | Fungsi zona | VLAN | Subnet / prefix | Gateway / router |
| --- | --- | --- | --- | --- |
| Transit Antar-Firewall | Penghubung Edge dan Internal Firewall. | - | 10.10.1.0/30 | Edge 10.10.1.1; Internal 10.10.1.2 |
| DMZ | Layanan publik Web/App (Nginx, ModSecurity, Flask). | 10 | 10.10.10.0/29 | 10.10.10.1 (Edge OPNsense) |
| DevOps & Management | Administrasi, GitHub Actions runner, serta AD DS/DNS. | 20 | 10.10.20.0/29 | 10.10.20.1 (Internal OPNsense) |
| Server/Data | Database PostgreSQL dan Backup Restic terenkripsi. | 30 | 10.10.30.0/29 | 10.10.30.1 (Internal OPNsense) |
| SOC | Pemantauan keamanan (Wazuh) dan IR (TheHive, Cortex, MISP). | 40 | 10.10.40.0/29 | 10.10.40.1 (Internal OPNsense) |
| Internal Client | Endpoint Windows 11 Enterprise dan Ubuntu Client. | 50 | 10.10.50.0/27 | 10.10.50.1 (Internal OPNsense) |
| Security Testing | Kali Linux untuk simulasi serangan terkontrol. | 60 | 10.10.60.0/29 | 10.10.60.1 (Internal OPNsense) |
| Tailscale VPN (Tailnet) | Remote administration VPN; Subnet Router pada Edge OPNsense. | - | 100.64.0.0/10 | Alokasi otomatis CGNAT Tailscale |

## 2. Perhitungan VLSM

| Nama zona | Subnet / prefix | Netmask | Rentang host usable | Broadcast | Kapasitas host | Alokasi baseline | Sisa baseline |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Transit Antar-Firewall | 10.10.1.0/30 | 255.255.255.252 | 10.10.1.1 - 10.10.1.2 | 10.10.1.3 | 2 | 2 | 0 |
| DMZ | 10.10.10.0/29 | 255.255.255.248 | 10.10.10.1 - 10.10.10.6 | 10.10.10.7 | 6 | 2 | 4 |
| DevOps & Management | 10.10.20.0/29 | 255.255.255.248 | 10.10.20.1 - 10.10.20.6 | 10.10.20.7 | 6 | 3 | 3 |
| Server/Data | 10.10.30.0/29 | 255.255.255.248 | 10.10.30.1 - 10.10.30.6 | 10.10.30.7 | 6 | 3 | 3 |
| SOC | 10.10.40.0/29 | 255.255.255.248 | 10.10.40.1 - 10.10.40.6 | 10.10.40.7 | 6 | 3 | 3 |
| Internal Client | 10.10.50.0/27 | 255.255.255.224 | 10.10.50.1 - 10.10.50.30 | 10.10.50.31 | 30 | 3 | 27 |
| Security Testing | 10.10.60.0/29 | 255.255.255.248 | 10.10.60.1 - 10.10.60.6 | 10.10.60.7 | 6 | 2 | 4 |
| Tailscale VPN (Tailnet) | 100.64.0.0/10 | 255.192.0.0 | Pool dinamis Tailscale | - | - | Sesuai node admin | Cadangan |

*Kapasitas host dihitung dengan rumus `2^(32-prefix)-2`. Subnet Security Testing diperbarui menjadi prefix `/29` pada RPP Rev.3 untuk menampung cadangan host penguji tambahan.*

## 3. Daftar IP 12 VM beserta nama zona

| No. VM | Nama VM | Nama zona | VLAN | IP utama / prefix | Gateway | Fungsi | vCPU | RAM (GiB) | Disk (GiB) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 01 | Edge OPNsense | Perimeter / Transit / DMZ | - | 10.10.1.1/30 | Upstream WAN (Lab) | Router Edge, NAT, Tailscale Subnet Router, Suricata IPS | 2 | 4 | 40 |
| 02 | Internal OPNsense | Transit / Gateway Internal | - | 10.10.1.2/30 | 10.10.1.1 | Inter-VLAN Routing (VLAN 20-60), Static Return Route, Suricata IPS | 2 | 4 | 40 |
| 03 | Web/App Server | DMZ | 10 | 10.10.10.2/29 | 10.10.10.1 | Nginx Reverse Proxy, ModSecurity WAF, Flask, Gunicorn | 2 | 2 | 32 |
| 04 | Management + Runner | DevOps & Management | 20 | 10.10.20.2/29 | 10.10.20.1 | Administrasi Bastion/Jumpbox, GitHub Actions Self-Hosted Runner | 2 | 2 | 40 |
| 05 | Windows Server 2025 | DevOps & Management | 20 | 10.10.20.3/29 | 10.10.20.1 | Active Directory Domain Services (AD DS), DNS Server Internal | 2 | 4 | 64 |
| 06 | Database Server | Server/Data | 30 | 10.10.30.2/29 | 10.10.30.1 | PostgreSQL Relational Database | 2 | 2 | 32 |
| 07 | Backup Server | Server/Data | 30 | 10.10.30.3/29 | 10.10.30.1 | Restic Backup Target (Append-only mode via SSH/SFTP) | 1 | 1 | 64 |
| 08 | Wazuh SIEM | SOC | 40 | 10.10.40.2/29 | 10.10.40.1 | Wazuh Manager, Indexer (OpenSearch), Dashboard | 4 | 8 | 80 |
| 09 | SOC-IR Stack | SOC | 40 | 10.10.40.3/29 | 10.10.40.1 | TheHive, Cortex, MISP (Multi-container Docker) | 4 | 12 | 160 |
| 10 | Windows 11 Enterprise | Internal Client | 50 | 10.10.50.10/27 | 10.10.50.1 | Client Domain Tergabung (AD Join) | 2 | 4 | 80 |
| 11 | Ubuntu Client | Internal Client | 50 | 10.10.50.20/27 | 10.10.50.1 | Endpoint Linux Client | 2 | 2 | 32 |
| 12 | Kali Linux | Security Testing | 60 | 10.10.60.2/29 | 10.10.60.1 | Penetrasi terkontrol (Nmap, Nikto, SQLmap, Hydra) | 2 | 2 | 40 |

**Total Kebutuhan Sumber Daya (12 VM):** 27 vCPU, 47 GiB RAM, 704 GiB Virtual Disk.  
*Pada PC Lab 32 GB, VM dijalankan menggunakan profil bergantian (maksimal 20–24 GiB RAM VM aktif), lihat panduan di [spesifikasi VM untuk PC 32 GB](spesifikasi-vm-32gb.md).*

## 4. Alamat interface router

| Router | Nama zona / interface | VLAN | Alamat | Keterangan |
| --- | --- | --- | --- | --- |
| Edge | WAN / Upstream | - | Mengikuti DHCP/Upstream Lab | Akses keluar internet & NAT |
| Edge | Transit Antar-Firewall | - | 10.10.1.1/30 | Interface p2p ke Internal OPNsense (10.10.1.2) |
| Edge | DMZ | 10 | 10.10.10.1/29 | Gateway Web/App (10.10.10.2) |
| Edge | Tailscale Subnet Router | - | Pool 100.64.0.0/10 | Iklankan rute: 10.10.10.0/29 & 10.10.20.0/29 |
| Internal | Transit Antar-Firewall | - | 10.10.1.2/30 | Default Gateway mengarah ke 10.10.1.1 |
| Internal | DevOps & Management | 20 | 10.10.20.1/29 | Gateway Management/Runner & Windows DC |
| Internal | Server/Data | 30 | 10.10.30.1/29 | Gateway Database PostgreSQL & Backup Restic |
| Internal | SOC | 40 | 10.10.40.1/29 | Gateway Wazuh SIEM & SOC-IR Stack |
| Internal | Internal Client | 50 | 10.10.50.1/27 | Gateway Windows 11 & Ubuntu Client |
| Internal | Security Testing | 60 | 10.10.60.1/29 | Gateway Kali Linux (Security Testing) |

## 5. Ringkasan host per zona

| Nama zona | Host / alokasi alamat |
| --- | --- |
| Transit Antar-Firewall | Edge 10.10.1.1; Internal 10.10.1.2 |
| DMZ | Web/App Server 10.10.10.2 |
| DevOps & Management | Management + Runner 10.10.20.2; Windows Server 2025 10.10.20.3 |
| Server/Data | Database Server 10.10.30.2; Backup Server 10.10.30.3 |
| SOC | Wazuh SIEM 10.10.40.2; SOC-IR 10.10.40.3 |
| Internal Client | Windows 11 10.10.50.10; Ubuntu Client 10.10.50.20 |
| Security Testing | Kali Linux 10.10.60.2 |
| Tailscale VPN | Subnet Router pada Edge; alokasi tailnet 100.64.0.0/10 |

## 6. Catatan implementasi arsitektur RPP Rev.3

1. **Konsolidasi Bastion:** Bastion Host tidak lagi berupa VM mandiri terpisah di DMZ. Akses administrasi jarak jauh kini dilakukan melalui **Tailscale Subnet Router** pada Edge OPNsense menuju Management Server (`10.10.20.2`) atau allowlist Nginx Web/App (`10.10.10.2`) untuk path `/admin`.
2. **Penggantian VPN WireGuard ke Tailscale:** Layanan VPN administratif sepenuhnya menggunakan Tailscale VPN. Tidak ada port inbound (seperti UDP 51820) yang dibuka pada WAN Edge.
3. **Migrasi Windows DC ke VLAN 20:** Windows Server 2025 (AD DS / DNS) dipindahkan ke VLAN 20 (`10.10.20.3/29`). Komunikasi antara Runner/Management dan Windows DC dilindungi oleh Windows Firewall lokal.
4. **Static Return Route:** Internal OPNsense dikonfigurasi dengan static route `100.64.0.0/10` via `10.10.1.1` (Edge) untuk memastikan paket balasan menuju admin Tailscale dapat diteruskan dengan benar.
5. **DNS & NTP Resolution:** Seluruh endpoint internal diarahkan ke Windows DNS Server (`10.10.20.3`) untuk resolusi nama domain internal, dan waktu disinkronkan via NTP dengan batas toleransi offset < 0.03 detik.
