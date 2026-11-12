# DOKUMEN MATRIKS ANCAMAN (THREAT MATRIX), PEMETAAN SUMBER LOG, & ALUR RESPONS INSIDEN SOC

**Proyek:** PBL-RKS301 – ITCorner.id (Secure E-Commerce IT Shop)  
**Penanggung Jawab:** Nur Arsyika Juana (NIM: 4332511023) – Security Analyst (SOC & Incident Response)  
**DevSecOps & Reviewer:** Afry Zacky Ardiansyahri (NIM: 4332511019)  
**Arsitektur Acuan:** RPP Rev.3 (12 Virtual Machines & Dual-Plane Architecture)

---

## 1. Pemetaan Sumber Log Keamanan (Log Source Mapping – 12 VM)

Seluruh log keamanan dari 7 zona jaringan dikumpulkan secara terpusat menuju **Wazuh SIEM Server (`10.10.40.2`)** pada VLAN 40 menggunakan protokol Wazuh Agent (`TCP 1514/1515`) dan Syslog (`UDP/TCP 514`):

| No | Nama Komponen / Host | Zona / VLAN | IP Address | Jenis Log yang Dikirim ke Wazuh (`10.10.40.2`) | Lokasi File / Protokol Sumber |
| :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | **Edge Router & Firewall** | Transit / WAN | `10.10.1.1` | Firewall Filter Log, NAT Log, Tailscale Log, & Suricata EVE Alert | Syslog (`UDP 514`) & `/var/log/suricata/eve.json` |
| 2 | **Internal Router & Firewall** | Transit / Inter-VLAN | `10.10.1.2` | Inter-VLAN Firewall Log & Suricata Internal IDS/IPS EVE Alert | Syslog (`UDP 514`) & `/var/log/suricata/eve.json` |
| 3 | **Web/App Server** | VLAN 10 (DMZ) | `10.10.10.2` | Nginx Access/Error Log, WAF ModSecurity JSON, Flask App Log, & FIM Uploads | `/var/log/nginx/*.log`, `/var/log/modsec_audit.log`, FIM `uploads/` |
| 4 | **Management + Runner** | VLAN 20 (DevOps) | `10.10.20.2` | GitHub Actions Runner Log, Docker Daemon Log, & SSH Deployment Log | `/var/log/auth.log`, `/var/log/syslog` |
| 5 | **Windows Server AD/DNS** | VLAN 20 (DevOps) | `10.10.20.3` | Windows Security Event Log (Kerberos, Event ID 4624/4625/4740, DNS) | Wazuh Agent (Windows EventChannel) |
| 6 | **Database Server** | VLAN 30 (Server) | `10.10.30.2` | PostgreSQL Query/Connection Audit Log & System Auth Log | `/var/log/postgresql/*.log`, `/var/log/auth.log` |
| 7 | **Database Backup Server** | VLAN 30 (Server) | `10.10.30.3` | Restic REST Server Log (`--append-only` port 8000) & System Auth Log | `/var/log/restic/restic.log`, `/var/log/auth.log` |
| 8 | **Wazuh SIEM Server** | VLAN 40 (SOC) | `10.10.40.2` | Wazuh Manager Internal Log, Alert Correlation Engine, & Telegram Integration | `/var/ossec/logs/alerts/alerts.json` |
| 9 | **SOC-IR Server** | VLAN 40 (SOC) | `10.10.40.3` | Docker Container Log (TheHive, Cortex, MISP) & Host Auth Log | `/var/log/auth.log`, Docker JSON Logs |
| 10 | **Windows 11 Client** | VLAN 50 (Client) | `10.10.50.10` | Windows Endpoint Event Log, Sysmon, & Aktivitas Akses Pengguna | Wazuh Agent (Windows EventChannel) |
| 11 | **Ubuntu Desktop Client** | VLAN 50 (Client) | `10.10.50.20` | Linux Endpoint Syslog & Auth Log | `/var/log/syslog`, `/var/log/auth.log` |
| 12 | **Security Testing (Kali)** | VLAN 60 (Testing) | `10.10.60.2` | Sumber trafik pengujian penetrasi terkontrol (dicatat pada target & router) | Dipantau melalui Suricata EVE & WAF Target |

---

## 2. Matriks Skenario Ancaman (Threat Matrix – 10 Skenario Utama)

| ID | Skenario Serangan | Target Aset & Fitur | MITRE ATT&CK | Pencegahan (Defense in Depth) | Deteksi Wazuh SIEM (`Rule ID` & Level) | Tindak Lanjut SOC |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **TH-01** | **SQL Injection (SQLi)** | Web/App (`10.10.10.2`) – Filter & Auth | `T1190` | WAF ModSecurity (`942xxx`) + Parameterized Query DB | **Rule `100101`** (Lvl 10) & Suricata `sid:1000004` | Kirim Alert Telegram, triase Cortex, buat Case TheHive |
| **TH-02** | **Cross-Site Scripting (XSS)** | Web/App (`10.10.10.2`) – Ulasan & Profil | `T1059.007` | WAF ModSecurity (`941xxx`) + `html.escape()` | **Rule `100101`** (Lvl 10) dari `modsec_audit.log` | Kirim Alert Telegram, validasi sanitasi DB |
| **TH-03** | **Web Login Brute-Force** | Web/App (`10.10.10.2`) – `/auth/login` | `T1110` | Hashing PBKDF2-SHA256 + Lockout 15 min (`HTTP 429`) | **Rule `100102`** (Lvl 10) – 5x gagal dalam 60s | Alert Telegram, blokir IP di OPNsense jika masif |
| **TH-04** | **Malicious File Upload / Web Shell** | Web/App (`10.10.10.2`) – Avatar & Bukti Bayar | `T1505.003` | Whitelist MIME, Magic Bytes, Batas Ukuran 2MB | **Wazuh FIM (`syscheck` Rule `554`)** pada `uploads/` | Alert Kritis Telegram, isolasi file, Case TheHive |
| **TH-05** | **SSH Brute-Force DMZ Web Server** | Web Server (`10.10.10.2:22`) | `T1110.001` | OPNsense Firewall (Hanya izinkan Runner / Tailscale) | **Rule `100103`** (Lvl 12) & Suricata `sid:1000002` | Alert Kritis Telegram, blokir IP sumber |
| **TH-06** | **Unauthorized Direct DB Access** | Database (`10.10.30.2:5432`) | `T1046` | Firewall OPNsense Internal (Hanya buka dari `10.10.10.2`) | Suricata EVE (`sid:1000003`) & Wazuh Alert | Alert Kritis Telegram, isolasi host pengirim |
| **TH-07** | **Akses Ilegal Dashboard Admin** | Web/App (`10.10.10.2`) – `/admin/*` | `T1548` | Proteksi RBAC (`session['role'] == 'admin'`) | **Rule `100104`** (Lvl 8) – HTTP 403 Forbidden berulang | Verifikasi akun pengguna, triase potensi bajak sesi |
| **TH-08** | **Brute-Force Active Directory** | Windows DC (`10.10.20.3`) | `T1078.002` | Windows Account Lockout Policy (GPO) | **Rule `60122` / `60144`** (Event ID 4625 & 4740) | Alert Telegram, unlock akun setelah konfirmasi user |
| **TH-09** | **Port Scanning Eksternal / Internal** | Edge & Internal Router | `T1046` | OPNsense Default Deny All + Drop SYN Flood | Suricata EVE Alert (`sid:1000001`) | Catat IP pengintai, masukkan blacklist firewall |
| **TH-10** | **Percobaan Penghapusan Backup** | Backup Server (`10.10.30.3:8000`) | `T1485` | Restic REST Server `--append-only` (Immutable Mode) | **Rule `100105`** (Lvl 12) – HTTP 403 saat DELETE snapshot | Alert Kritis Telegram, isolasi kredensial DB |

---

## 3. Alur Kerja Penanganan Insiden (SOC Incident Response Runbook)

1. **Detection & Collection:** Seluruh event serangan dari WAF ModSecurity, Suricata IDS/IPS, OPNsense, dan Endpoint diteruskan secara real-time ke **Wazuh SIEM (`10.10.40.2`)**.
2. **Real-Time Alerting (Telegram Bot API):** Jika memicu aturan dengan tingkat keparahan tinggi (`Level >= 10`), Wazuh mengeksekusi skrip integrasi `custom-telegram.py` melalui HTTPS (`TCP 443`) untuk mengirim notifikasi instan ke **Grup Telegram SOC ITCorner.id**.
3. **Triage & Case Management (TheHive – `10.10.40.3`):** Analis SOC memeriksa alert di Telegram dan Wazuh Dashboard, lalu membuat tiket kasus (*Case*) di **TheHive** dengan menyertakan *Observable* (IP penyerang, URL target, Rule ID, dan potongan raw log).
4. **Enrichment & Threat Intelligence (Cortex & MISP – `10.10.40.3`):** Analis menjalankan *Analyzer* **Cortex** pada *Observable* untuk memeriksa reputasi IP/file dan mencocokkannya dengan database indikator ancaman (*IoC*) di **MISP**.
5. **Containment, Eradication, & Recovery:**
   * Memblokir IP penyerang pada Firewall OPNsense (`10.10.1.1` / `10.10.1.2`).
   * Jika terjadi modifikasi kode/kontainer pada Web Server DMZ (`10.10.10.2`), tim DevSecOps mengeksekusi **Rollback kontainer Docker** via [`scripts/deploy.sh`](file:///c:/Users/HYPE%20AMD/Documents/PBL/PBL-RKS301/itcorner-id/scripts/deploy.sh).
   * Jika terjadi kerusakan data pada PostgreSQL (`10.10.30.2`), tim DBA mengeksekusi **Restore snapshot terenkripsi Restic** dari Backup Server (`10.10.30.3`).
6. **Post-Incident & Evidence Pack:** Mendokumentasikan *Alert ID*, *Case ID*, bukti tangkapan layar (*evidence*), dan memperbarui aturan WAF/Suricata/Wazuh untuk menutup celah di masa mendatang.
