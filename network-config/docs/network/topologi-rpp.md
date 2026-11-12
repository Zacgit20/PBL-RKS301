# Topologi Acuan RPP Rev.3 (12 VM)

**Versi:** 1.0 (Revisi 3) - November 2026  
**Sumber:** `topology/topologi-soc-1.png` / `SOC_1_rev3.drawio` (RPP PBL RKS-301 Rev.3)  
**Status:** Diagram Arsitektur Target Resmi Tim Well Architected SOC 1.

![Topologi Resmi RPP Rev.3](topologi-soc-1.png)

Diagram topologi di atas merupakan gambar acuan resmi proyek yang telah diselaraskan dengan kebutuhan kurikulum 5 mata kuliah integrasi.

## Keselarasan Arsitektur dengan Baseline 12 VM

1. **Jumlah Virtual Machine (12 VM):**
   * Sesuai keputusan final RPP Rev.3, infrastruktur disederhanakan menjadi **12 VM** (menghilangkan Bastion Host sebagai VM mandiri).
   * Akses administrasi jarak jauh dari luar dialihkan melalui **Tailscale Subnet Router** pada Edge OPNsense langsung menuju Management Server (`10.10.20.2`) atau Web Server (`10.10.10.2` path `/admin`).
2. **Migrasi Windows Server ke Zona Management:**
   * Windows Server 2025 (Active Directory & DNS Server internal) ditempatkan pada **VLAN 20 Management** (`10.10.20.3/29`), berdampingan dengan Management Server + Runner (`10.10.20.2/29`).
3. **Dual-Tier Firewall & Routing:**
   * **Edge OPNsense (10.10.1.1):** Menangani proteksi perimeter, port forwarding HTTPS publik (DNAT 443), Tailscale VPN daemon, dan Suricata IPS DMZ.
   * **Internal OPNsense (10.10.1.2):** Menangani inter-VLAN routing (VLAN 20 s.d. 60), penegakan firewall *Least Privilege*, *static return route* untuk subnet Tailscale (`100.64.0.0/10`), dan Suricata IPS internal.
4. **Pemisahan Zona Terisolasi:**
   * **DMZ (VLAN 10):** Web/App Server (`10.10.10.2`).
   * **DevOps & Management (VLAN 20):** Management + Runner (`10.10.20.2`) & Windows DC (`10.10.20.3`).
   * **Server/Data (VLAN 30):** PostgreSQL Database (`10.10.30.2`) & Backup Restic (`10.10.30.3`).
   * **SOC Zone (VLAN 40):** Wazuh SIEM (`10.10.40.2`) & SOC-IR Stack (`10.10.40.3`).
   * **Internal Client (VLAN 50):** Windows 11 (`10.10.50.10`) & Ubuntu Client (`10.10.50.20`).
   * **Security Testing (VLAN 60):** Kali Linux (`10.10.60.2/29`).

Rincian lengkap alokasi IP, VLSM, dan tabel interface dapat dilihat pada [Tabel IP dan VLSM](tabel-ip-vlsm.md).
