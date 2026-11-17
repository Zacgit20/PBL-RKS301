# Integrasi Suricata IPS dan Operasional SOC

**Versi:** 1.0 (Revisi 3) - November 2026  
**Penanggung Jawab:** Muhammad Danish (Network & Security Defender) & Nur Arsyika Juana (SOC Analyst)  
**Status:** Baseline Arsitektur RPP Rev.3 (12 VM) & Threat Matrix SOC Terpadu.

Dokumen ini mengatur koordinasi teknis antara modul deteksi jaringan Suricata IPS pada firewall OPNsense dengan Security Operations Center (SOC) berbasis Wazuh SIEM dan Incident Response Stack (TheHive, Cortex, MISP).

---

## 1. Pembagian Peran Sensor & Batas Deteksi

1. **Inspeksi Level Jaringan (L3/L4/L7 Plaintext) - Suricata IPS:**
   * Memantau anomali koneksi TCP/IP seperti port scanning (Nmap SYN scan), percobaan brute-force SSH, dan percobaan koneksi langsung tanpa izin antar-zona (seperti akses ilegal ke PostgreSQL).
   * Pada alur HTTPS terenkripsi, Suricata tidak melakukan terminasi TLS publik.
2. **Inspeksi Level Aplikasi (L7 HTTPS Payload) - ModSecurity WAF:**
   * Dijalankan pada Web/App Server DMZ (`10.10.10.2`) di balik Nginx Reverse Proxy setelah proses TLS termination selesai.
   * Bertanggung jawab penuh mendeteksi serangan injeksi aplikasi web (SQL Injection, XSS, Path Traversal, File Inclusion) menggunakan OWASP Core Rule Set (CRS). Log audit WAF (`/var/log/nginx/modsec_audit.log`) diteruskan ke Wazuh SIEM.

---

## 2. Aturan Kustom Suricata (`itcorner-local.rules`)

| SID | Nama Deteksi / Signature | Protokol & Target | Kriteria Pemicu (Threshold/Pattern) | Kategori Ancaman |
| --- | --- | --- | --- | --- |
| **1000001** | `ITCORNER-IDS Possible Nmap SYN Scan to DMZ Web Server` | `tcp any any -> 10.10.10.2 any` | `flags:S`, 20 SYN dalam 10 detik per sumber IP. | *Reconnaissance / Port Scanning* |
| **1000002** | `ITCORNER-IDS Potential SSH Brute-Force on DMZ Web Server` | `tcp any any -> 10.10.10.2 22` | `flags:S`, 5 koneksi dalam 60 detik per sumber IP. | *Credential Access / Brute Force* |
| **1000003** | `ITCORNER-IDS Unauthorized Direct Database Access Attempt` | `tcp !10.10.10.2 any -> 10.10.30.2 5432` | `flags:S`, Upaya koneksi ke PostgreSQL selain dari Web Server. | *Lateral Movement / Policy Violation* (**Inline Drop**) |
| **1000004** | `ITCORNER-IDS SQL Injection Attempt in HTTP URI` | `http any any -> 10.10.10.2 any` | Keyword `UNION` dan `SELECT` pada URI HTTP. | *Web Application Attack* |

---

## 3. Matriks Aliran Data Telemetri ke SOC

| Sumber Log / Sensor | Format Data | Metode Pengiriman / Port | Tujuan / Agen Pengumpul |
|---|---|---|---|
| **OPNsense Firewall (Filterlog)** | Syslog RFC 5424 (UDP) | UDP / 514 | Wazuh SIEM (`10.10.40.2`) - Syslog Listener |
| **Suricata IDS/IPS Engine** | JSON (`eve.json`) | Wazuh Agent File Collector | Wazuh SIEM (`10.10.40.2`) |
| **Nginx Access & Error Log** | Plaintext / Custom Log | Wazuh Agent (`/var/log/nginx/`) | Wazuh SIEM (`10.10.40.2`) |
| **ModSecurity WAF Audit Log** | JSON / ModSec Serialized | Wazuh Agent (`modsec_audit.log`) | Wazuh SIEM (`10.10.40.2`) |
| **PostgreSQL Audit Log** | Plaintext (`postgresql.log`) | Wazuh Agent (`/var/log/postgresql/`) | Wazuh SIEM (`10.10.40.2`) |
| **Windows Server (AD DS)** | Windows Event Log (Security/Sys) | Wazuh Agent (Channel: Security) | Wazuh SIEM (`10.10.40.2`) |

---

## 4. Alur Eskalasi & Incident Response

```
[ Sensor / Endpoint Log ]
          │
          ▼
[ Wazuh Manager (10.10.40.2) ]
          │
          ├── Evaluasi Ruleset (local_rules.xml)
          ├── Level < 10 ──► Simpan ke Indexer (OpenSearch)
          │
          └── Level >= 10 ──┬──► Notifikasi Instan: Telegram Bot API (SOC Channel)
                            │
                            └──► Pembuatan Tiket Otomatis: TheHive (10.10.40.3)
                                      │
                                      ▼
                             Enrichment IoC via MISP
                                      │
                                      ▼
                             Respon Terpilih via Cortex
```

## 5. Kriteria Keberhasilan Integrasi (Acceptance Criteria)

1. **Parser Engine Valid:** Menjalankan verifikasi `suricata -T` pada ruleset kustom tanpa menghasilkan peringatan error sintaks.
2. **Korelasi Terpusat:** Event port scan (SID 1000001) dari Kali Linux (`10.10.60.2`) muncul di *Wazuh Dashboard > Security Events* lengkap dengan label host penyerang.
3. **Penegakan Inline Drop:** Percobaan akses langsung port 5432 dari luar Web Server memicu SID 1000003 dan koneksi langsung diputus oleh Internal OPNsense, tercatat di log *drop action*.
4. **Alert Eskalasi:** Alert tingkat kritis (Level >= 10) berhasil masuk ke grup Telegram SOC dalam waktu < 5 detik.
