# Panduan Konfigurasi Firewall Edge & Internal OPNsense

**Versi:** 1.0 (Revisi 3) - November 2026  
**Penanggung Jawab:** Muhammad Danish - System Integrator & Network Defender  
**Status:** Baseline Terverifikasi ATS & Arsitektur RPP Rev.3 (12 VM).

Dokumen ini memuat panduan implementasi teknis segmentasi jaringan, antarmuka VLAN, perutean bertingkat (*Dual-Tier Routing*), integrasi Tailscale Subnet Router, dan persiapan Suricata IPS pada firewall OPNsense Edge dan Internal.

---

## 1. Pemetaan Antarmuka & Segmen Jaringan (VMware Workstation)

Infrastruktur dibangun di atas VMware Workstation menggunakan Custom LAN Segment dan penandaan tag 802.1Q (guest & sub-interface tagging):

| Peran Router / Host | Antarmuka Fisik / Virtual | Media LAN Segment | Alamat IP / Prefix | Tag VLAN | Keterangan |
|---|---|---|---|---|---|
| **Edge OPNsense** (WAN) | `vtnet0` / `em0` | NAT / Bridged (Lab) | Mengikuti DHCP Lab | - | Akses internet publik, NAT keluar |
| **Edge OPNsense** (Transit) | `vtnet1` / `em1` | `PBL-TRANSIT` | `10.10.1.1/30` | - | Titik interkoneksi ke Internal OPNsense |
| **Edge OPNsense** (DMZ Parent) | `vtnet2` / `em2` | `PBL-TRUNK-DMZ` | Tanpa IP (Parent) | - | Membawa trunk DMZ |
| **Edge OPNsense** (DMZ Child) | `vtnet2_vlan10` | `PBL-TRUNK-DMZ` | `10.10.10.1/29` | 10 | Gateway Web/App Server (`10.10.10.2`) |
| **Edge OPNsense** (Tailscale) | `tailscale0` | Virtual Tunnel | Pool `100.64.0.0/10` | - | Subnet Router: iklan `10.10.10.0/29` & `10.10.20.0/29` |
| **Internal OPNsense** (Transit) | `em0` | `PBL-TRANSIT` | `10.10.1.2/30` | - | Default gateway mengarah ke `10.10.1.1` |
| **Internal OPNsense** (Parent) | `em1` | `PBL-TRUNK-INTERNAL` | Tanpa IP (Parent) | - | Trunk pembawa seluruh VLAN internal |
| **Internal OPNsense** (Management) | `em1_vlan20` | `PBL-TRUNK-INTERNAL` | `10.10.20.1/29` | 20 | Gateway Management/Runner (`.2`) & Win-Server (`.3`) |
| **Internal OPNsense** (Server/Data) | `em1_vlan30` | `PBL-TRUNK-INTERNAL` | `10.10.30.1/29` | 30 | Gateway PostgreSQL (`.2`) & Backup Restic (`.3`) |
| **Internal OPNsense** (SOC Zone) | `em1_vlan40` | `PBL-TRUNK-INTERNAL` | `10.10.40.1/29` | 40 | Gateway Wazuh SIEM (`.2`) & SOC-IR Stack (`.3`) |
| **Internal OPNsense** (Client LAN) | `em1_vlan50` | `PBL-TRUNK-INTERNAL` | `10.10.50.1/27` | 50 | Gateway Win11 (`.10`) & Ubuntu Client (`.20`) |
| **Internal OPNsense** (Security Testing) | `em1_vlan60` | `PBL-TRUNK-INTERNAL` | `10.10.60.1/29` | 60 | Gateway Kali Linux (`.2`) |

---

## 2. Urutan Konfigurasi Internal OPNsense

1. **Verifikasi Antarmuka Fisik:**
   * Pastikan adapter `em0` terhubung ke `PBL-TRANSIT` dan `em1` terhubung ke `PBL-TRUNK-INTERNAL`.
2. **Pembuatan VLAN 802.1Q:**
   * Masuk menu **Interfaces > Other Types > VLAN**.
   * Tambahkan 5 VLAN dengan Parent `em1`:
     * VLAN 20: Management (Priority 0)
     * VLAN 30: Server/Data
     * VLAN 40: SOC
     * VLAN 50: Internal Client
     * VLAN 60: Security Testing
3. **Penetapan Antarmuka (Assignments) & IP Gateway:**
   * Tetapkan WAN ke `em0` dengan Static IPv4 `10.10.1.2/30`, Gateway `10.10.1.1`.
   * Tetapkan masing-masing VLAN ke antarmuka logis (LAN, OPT1, OPT2, OPT3, OPT4) dan konfigurasikan IP gateway sesuai tabel di atas.
4. **Static Return Route (Untuk Tailscale):**
   * Tambahkan static route di **System > Routes > Configuration**:
     * Jaringan Tujuan: `100.64.0.0/10`
     * Gateway: `10.10.1.1` (Edge Transit)
   * *Fungsi:* Menjamin paket balasan dari server internal (seperti Management SSH) dapat kembali ke perangkat administrator Tailscale yang berada di luar jaringan lokal.
5. **Konfigurasi Firewall Rules:**
   * Terapkan kebijakan *Default Deny*.
   * Buka port AD DS (DNS 53, Kerberos 88, LDAP 389, SMB 445, RPC) dari VLAN 50 hanya menuju Windows Server `10.10.20.3`.
   * Buka port PostgreSQL `5432` pada VLAN 30 hanya dari sumber Web/App Server `10.10.10.2`.
   * Buka port Wazuh Agent `1514/1515` menuju `10.10.40.2`.
   * Konfigurasikan syslog OPNsense (filterlog) agar dikirimkan ke Wazuh SIEM melalui UDP port 514.

---

## 3. Urutan Konfigurasi Edge OPNsense

1. **Konfigurasi Antarmuka:**
   * WAN: Dapatkan IP melalui DHCP dari jaringan lab/VMware NAT.
   * Transit: Static IPv4 `10.10.1.1/30` pada `vtnet1`.
   * DMZ: Buat sub-interface VLAN 10 pada parent `vtnet2`, tetapkan IP `10.10.10.1/29`.
2. **Perutean Statis Menuju Zona Internal:**
   * Tambahkan Gateway `10.10.1.2` (Internal Transit).
   * Tambahkan 5 rute statis menuju jaringan internal melalui gateway `10.10.1.2`:
     * `10.10.20.0/29`
     * `10.10.30.0/29`
     * `10.10.40.0/29`
     * `10.10.50.0/27`
     * `10.10.60.0/29`
3. **Port Forwarding (DNAT HTTPS Publik):**
   * Masuk ke **Firewall > NAT > Port Forward**.
   * Forward port WAN TCP 443 -> IP Web/App `10.10.10.2:443`.
   * Aturan filter terkait dibuat otomatis (PASS). Port SSH, database, dan manajemen web GUI TIDAK BOLEH dipublikasikan ke WAN.
4. **Instalasi & Pengaturan Tailscale Subnet Router:**
   * Instal plugin Tailscale atau binary CLI melalui shell OPNsense:
     ```bash
     tailscale up --advertise-routes=10.10.10.0/29,10.10.20.0/29 --snat-subnet-routes=false --accept-dns=false
     ```
   * Setujui rute (*Approve Routes*) pada Tailscale Admin Console.
   * Pastikan flag `--snat-subnet-routes=false` aktif agar IP tailnet asli (`100.64.x.x`) terlihat utuh pada log Nginx dan telemetri Wazuh.

---

## 4. Konfigurasi Tagging pada Guest OS (Windows & Linux)

1. **Windows Server 2025 (VLAN 20) & Windows 11 (VLAN 50):**
   * Wajib menggunakan adapter virtual **VMXNET3** pada VMware Workstation.
   * Pada Windows Server: Buka Device Manager > Network Adapter > Advanced > **VLAN ID** diisi `20`. Set IP statis `10.10.20.3/29`, Gateway `10.10.20.1`, DNS `127.0.0.1`.
   * Pada Windows 11: Buka Advanced Adapter Properties > **VLAN ID** diisi `50`. Set IP statis `10.10.50.10/27`, Gateway `10.10.50.1`, DNS `10.10.20.3`.
2. **Linux Hosts (Web/App, Management, Database, Wazuh, Kali):**
   * Menggunakan Netplan (`/etc/netplan/01-netcfg.yaml`) dengan driver VMXNET3:
     ```yaml
     network:
       version: 2
       renderer: networkd
       ethernets:
         ens160:
           dhcp4: no
       vlans:
         vlan20:
           id: 20
           link: ens160
           addresses: [10.10.20.2/29]
           routes:
             - to: default
               via: 10.10.20.1
           nameservers:
             addresses: [10.10.20.3]
     ```

---

## 5. Implementasi Suricata IPS Terpadu

* Engine Suricata dijalankan pada antarmuka parent Edge (`vtnet2`) dan Internal (`em1`).
* Mengaktifkan aturan kustom `itcorner-local.rules`:
  * `1000001`: Deteksi Port Scan SYN Nmap ke DMZ.
  * `1000002`: Deteksi Brute Force SSH ke Web Server.
  * `1000003`: Blokir Percobaan Direct Access ke PostgreSQL Port 5432 (Inline Drop).
  * `1000004`: Deteksi SQL Injection pada URI HTTP.
* Seluruh alert disinkronkan ke file `eve.json` dan dialirkan ke Wazuh SIEM melalui Wazuh Agent yang terpasang pada router / server lokal.
