# Spesifikasi 12 VM dan Rencana Pemakaian PC Lab 32 GB

**Versi:** 1.0 (Revisi 3) - November 2026  
**Penanggung Jawab:** Muhammad Danish - System Integrator & Network Engineer  
**Status:** Baseline Arsitektur RPP Rev.3 (12 VM) & Rencana Operasional Lab.

## 1. Keputusan Kapasitas

Infrastruktur ITCorner.id membutuhkan total 12 VM virtual. Menjalankan seluruh 12 VM secara bersamaan memerlukan total 47 GiB RAM dan 27 vCPU, sehingga pada PC Lab berspesifikasi RAM 32 GB, **VM dijalankan bergantian menggunakan profil operasional** dengan batasan maksimal alokasi 20–24 GiB RAM VM aktif.

Strategi ini menyisakan batas aman sekitar 8–12 GiB RAM untuk Windows host, VMware hypervisor overhead, browser, dan buffer caching. Disk virtual target sebesar 704 GiB dialokasikan secara tipis (*thin provisioned*), di mana pemakaian aktual pada storage awal hanya berkisar 100–150 GB.

## 2. Rincian Spesifikasi 12 Virtual Machine

| No. VM | Nama VM | Zona Jaringan | VLAN | OS / Mode | vCPU | RAM (GiB) | Disk Virtual (GiB) | Fungsi & Keterangan |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 01 | Edge OPNsense | Perimeter / DMZ | - | OPNsense 24.x/26.x | 2 | 4 | 40 | Router Edge, NAT, Tailscale Subnet Router, Suricata IPS |
| 02 | Internal OPNsense | Transit / Internal | - | OPNsense 24.x/26.x | 2 | 4 | 40 | Inter-VLAN Routing (VLAN 20-60), Static Return Route, Suricata IPS |
| 03 | Web/App Server | DMZ | 10 | Ubuntu Server LTS | 2 | 2 | 32 | Nginx Reverse Proxy, ModSecurity WAF, Flask, Gunicorn |
| 04 | Management + Runner | DevOps & Management | 20 | Ubuntu Server LTS | 2 | 2 | 40 | Jumpbox CLI, GitHub Actions Self-Hosted Runner terisolasi |
| 05 | Windows Server 2025 | DevOps & Management | 20 | Windows Server 2025 | 2 | 4 | 64 | AD DS, DNS Server Internal (Migrasi dari VLAN 30 ke VLAN 20) |
| 06 | Database Server | Server/Data | 30 | Ubuntu Server LTS | 2 | 2 | 32 | PostgreSQL Database Server |
| 07 | Backup Server | Server/Data | 30 | Ubuntu Server LTS | 1 | 1 | 64 | Target pencadangan Restic mode append-only (SSH/SFTP) |
| 08 | Wazuh SIEM | SOC Zone | 40 | Ubuntu Server LTS | 4 | 8 | 80 | Wazuh Manager, OpenSearch Indexer, Wazuh Dashboard |
| 09 | SOC-IR Stack | SOC Zone | 40 | Ubuntu Server LTS | 4 | 12 | 160 | TheHive, Cortex, MISP (Multi-container Docker) |
| 10 | Windows 11 Enterprise | Internal Client | 50 | Windows 11 Pro/Ent | 2 | 4 | 80 | Endpoint Client domain join (AD DS) |
| 11 | Ubuntu Client | Internal Client | 50 | Ubuntu (CLI/Lite) | 2 | 2 | 32 | Endpoint Linux Client untuk pengujian browsing & auth |
| 12 | Kali Linux | Security Testing | 60 | Kali Linux 2024.x | 2 | 2 | 40 | Host penetrasi terkontrol (Nmap, Nikto, SQLmap, Hydra) |

**Total Kebutuhan Sumber Daya (12 VM):** 27 vCPU, 47 GiB RAM, 704 GiB Disk Virtual.  
*Konsolidasi RPP Rev.3 meniadakan VM Bastion mandiri (sebelumnya VM 04), fungsi remote access digantikan oleh Tailscale Subnet Router pada Edge OPNsense.*

---

## 3. Komponen Berat & Alokasi Minimum

- **Wazuh SIEM (4 vCPU, 8 GiB RAM):** Komponen all-in-one Wazuh (Manager, OpenSearch Indexer, Dashboard) membutuhkan heap memory JVM minimum 4 GiB untuk OpenSearch agar tidak memicu status read-only cluster.
- **SOC-IR Stack (4 vCPU, 12 GiB RAM):** Menjalankan TheHive (Cassandra/Elasticsearch), Cortex, dan MISP (MySQL/Redis) via Docker. Penggunaan memori dikendalikan dengan batasan container limit pada `docker-compose.yml`.
- **Dual-Tier OPNsense (4 GiB per instance):** Menyediakan kapasitas memori yang cukup untuk tabel state firewall, routing dynamic/static, Tailscale daemon, dan engine Suricata IPS dengan ruleset aktif.

---

## 4. Rencana Profil Pengoperasian Bergantian (PC Lab 32 GB)

Untuk menjaga stabilitas PC lab agar pemakaian RAM VM aktif tidak melebihi 24 GiB:

### Profil A: Pengembangan Aplikasi, Database & Deployment CI/CD
*Fokus:* Coding web, migrasi skema database, pengujian pipeline GitHub Actions, dan registrasi AD domain.
* **VM Aktif:** Edge (4 GB), Internal (4 GB), Web/App (2 GB), Database (2 GB), Management/Runner (2 GB), Windows Server (4 GB).
* **Total RAM VM Aktif:** **18 GiB** (Menyisakan 14 GiB untuk Windows Host).

### Profil B: Pemantauan Keamanan & Deteksi Serangan (SOC & Red Team)
*Fokus:* Ingestion log multi-sumber ke SIEM, pengujian aturan deteksi Wazuh, pemindaian port scan & brute force dari Kali Linux.
* **VM Aktif:** Edge (4 GB), Internal (4 GB), Web/App (2 GB), Database (2 GB), Wazuh SIEM (8 GB), Kali Linux (2 GB).
* **Total RAM VM Aktif:** **22 GiB** (Menyisakan 10 GiB untuk Windows Host).

### Profil C: Penanganan Insiden Keamanan (Incident Response Stack)
*Fokus:* Pengujian eskalasi alert Wazuh ke TheHive, enrichment indikator ancaman via MISP, dan eksekusi responder Cortex.
* **VM Aktif:** Edge (4 GB), Internal (4 GB), Web/App (2 GB), Wazuh SIEM (8 GB), SOC-IR Stack (12 GB).
* **Total RAM VM Aktif:** **30 GiB** (Dijalankan dengan tuning memory limit container SOC-IR ke 8–10 GB sehingga total konsumsi menjadi ~**26–28 GiB**).

### Profil D: Pencadangan & Simulasi Disaster Recovery (Backup Drill)
*Fokus:* Otomasi snapshot database PostgreSQL, enkripsi Restic ke Backup Server, dan uji pemulihan data (restore).
* **VM Aktif:** Edge (4 GB), Internal (4 GB), Web/App (2 GB), Database (2 GB), Backup Server (1 GB), Management (2 GB).
* **Total RAM VM Aktif:** **15 GiB** (Menyisakan 17 GiB untuk Windows Host).

---

## 5. Pedoman Manajemen Penyimpanan Disk

1. Gunakan format **Thin Provisioning** saat membuat virtual disk di VMware Workstation agar ruang host hanya terpakai sebesar data nyata yang terisi.
2. Terapkan kebijakan **Index State Management (ISM)** pada Wazuh Indexer dengan masa retensi 7 hari untuk mencegah kehabisan ruang disk (*flood-stage watermark 95%*).
3. Bersihkan log container Docker dan cache build (`docker system prune -f`) secara berkala pada host SOC-IR dan Web/App.
