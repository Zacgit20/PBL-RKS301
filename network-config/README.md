# Dokumentasi Konfigurasi Jaringan & Keamanan ITCorner.id (PBL-RKS301)

**Penanggung Jawab:** Muhammad Danish - Leader & System Integrator  
**Target Branch:** `feat/network-config` (disinkronkan dengan `development`)  
**Versi:** 1.0 (Revisi 3) - November 2026  
**Status:** Baseline Terverifikasi ATS & Arsitektur Resmi RPP Rev.3 (12 VM).

Paket ini memuat seluruh rancangan arsitektur jaringan, topologi resmi, perhitungan VLSM, panduan konfigurasi Dual-Tier OPNsense, integrasi Tailscale Subnet Router, matriks aturan firewall *Least Privilege*, dan aturan deteksi kustom Suricata NIDS/IPS untuk proyek PBL RKS-301 ITCorner.id.

---

## 1. Pokok Perubahan Arsitektur RPP Rev.3 (12 VM)

1. **Konsolidasi Bastion Host:**
   * Bastion Host tidak lagi berupa VM mandiri terpisah di DMZ.
   * Remote access dialihkan melalui **Tailscale Subnet Router** pada Edge OPNsense langsung menuju Management Server (`10.10.20.2`) atau Web Server (`10.10.10.2:443`).
2. **Penggantian WireGuard dengan Tailscale:**
   * VPN administratif tidak lagi mengekspos port UDP 51820 di WAN.
   * Tailscale Subnet Router mengiklankan rute `10.10.10.0/29` dan `10.10.20.0/29`. Internal OPNsense dilengkapi rute statis balik `100.64.0.0/10` via `10.10.1.1`.
3. **Migrasi Windows Server ke VLAN 20:**
   * Windows Server 2025 (Active Directory & DNS) dipindahkan dari VLAN 30 ke **VLAN 20 Management** (`10.10.20.3/29`).
4. **Pembaruan Subnet Security Testing:**
   * Subnet Kali Linux diperbarui menjadi prefix **`/29` (`10.10.60.0/29`)** guna menyediakan ruang bagi host penguji tambahan.
5. **Harmonisasi Ruleset Kustom Suricata:**
   * Mengadopsi 4 aturan deteksi kustom terverifikasi (`1000001` s.d. `1000004`) pada `config/suricata/itcorner-local.rules`, selaras dengan ruleset pada `itcorner-id/`.

---

## 2. Struktur Berkas Paket `network-config/`

* **`docs/network/tabel-ip-vlsm.md`**: Pembagian zona, perhitungan VLSM, daftar alokasi IP 12 VM, dan antarmuka router.
* **`docs/network/firewall-rule-matrix.md`**: Matriks aturan firewall OPNsense Edge dan Internal (*Default Deny* & *Least Privilege*).
* **`docs/network/konfigurasi-edge-internal.md`**: Langkah teknis konfigurasi antarmuka OPNsense, VLAN 802.1Q, static route balik Tailscale, dan tagging VMXNET3.
* **`docs/network/spesifikasi-vm-32gb.md`**: Alokasi resource 12 VM (27 vCPU, 47 GiB RAM, 704 GiB Disk) dan rencana profil RAM bergantian pada PC Lab 32 GB.
* **`docs/network/rencana-ips-opnsense.md`**: Panduan penggelaran Suricata mode Netmap inline dan aksi drop untuk proteksi basis data.
* **`docs/network/suricata-dan-integrasi-soc.md`**: Alur integrasi log Suricata (`eve.json`) ke Wazuh SIEM, eskalasi TheHive, dan bot Telegram.
* **`docs/network/topologi-rpp.md`**: Dokumentasi diagram arsitektur acuan resmi RPP Rev.3.
* **`config/suricata/itcorner-local.rules`**: Signature rules kustom Suricata IDS/IPS.

---

## 3. Profil Pengoperasian pada PC Lab 32 GB

Untuk menghindari overcommit RAM fisik 32 GB, VM dijalankan menggunakan profil bergantian:
* **Profil A (DevOps & Web App):** Edge (4GB), Internal (4GB), Web/App (2GB), DB (2GB), Management/Runner (2GB), Windows Server (4GB) = **18 GiB**.
* **Profil B (Pemantauan SOC & Red Team):** Edge (4GB), Internal (4GB), Web/App (2GB), DB (2GB), Wazuh SIEM (8GB), Kali (2GB) = **22 GiB**.
* **Profil C (Penanganan Insiden SOC-IR):** Edge (4GB), Internal (4GB), Web/App (2GB), Wazuh SIEM (8GB), SOC-IR (12GB) = **26–28 GiB** *(dengan container memory tuning)*.
* **Profil D (Disaster Recovery / Backup Drill):** Edge (4GB), Internal (4GB), Web/App (2GB), DB (2GB), Backup Server (1GB), Management (2GB) = **15 GiB**.
