# Rencana Suricata IPS pada OPNsense Edge dan Internal

**Versi:** 1.0 (Revisi 3) - November 2026  
**PIC Network:** Muhammad Danish  
**Koordinasi SOC:** Nur Arsyika Juana  
**Status:** Target Arsitektur RPP Rev.3 (12 VM) & Integrasi Ruleset Kustom.

## 1. Tujuan dan Kondisi Saat Ini

Tim menetapkan Suricata sebagai Intrusion Prevention System (IPS) pada Edge dan Internal OPNsense. Target utamanya adalah mendeteksi serta memblokir paket berbahaya secara *inline* berdasarkan aturan deteksi kustom `itcorner-local.rules` (SID 1000001–1000004), lalu meneruskan telemetri event ke Wazuh SIEM melalui format EVE JSON / Syslog. Firewall tetap bertanggung jawab atas penyaringan paket L3/L4, sementara Suricata menginspeksi muatan protokol dan anomali alur data secara mendalam. Proteksi aplikasi web HTTPS tetap didukung oleh Reverse Proxy Nginx dan ModSecurity WAF dengan OWASP Core Rule Set (CRS).

## 2. Tahapan Pengerjaan

| Tahap | Target | Syarat Melanjutkan | Status Terkini |
| --- | --- | --- | --- |
| A - Jaringan | Segmentasi VLAN 802.1Q, routing bertingkat, dan aturan firewall dasar | Konektivitas normal dan akses console OPNsense stabil | **SELESAI (ATS)** |
| B - Observasi | Pemuatan ruleset kustom dan uji deteksi dalam mode alert | Seluruh 4 SID kustom aktif; parser engine sukses tanpa sintaks error | **SELESAI (ATS)** |
| C - IPS Terbatas | Pengaktifan mode Netmap inline dan aksi drop pada SID kritis (SID 1000003) | Akses sah Web-ke-DB lolos; akses liar di luar Web Server diblokir seketika | **AKTIF (Pekan 9-10)** |
| D - Integrasi SOC | Pengiriman alert Suricata ke Wazuh SIEM dan eskalasi ke TheHive | Korelasi log di Wazuh Dashboard dan tiket otomatis terbentuk | **RENCANA (Pekan 11-12)** |

## 3. Mode dan Titik Inspeksi Target

Mode yang digunakan adalah **Netmap IPS** pada interface fisik/parent trunk OPNsense:
* **Edge OPNsense:** Diterapkan pada parent DMZ trunk (`vtnet2` / `em2`) yang membawa VLAN 10 (Web/App Server `10.10.10.2`).
* **Internal OPNsense:** Diterapkan pada parent trunk `em1` yang membawa VLAN 20, 30, 40, 50, dan 60.

Hardware offloading (LRO, TSO, Checksum Offload) dinonaktifkan pada kedua firewall untuk memastikan kompatibilitas penuh dengan subsistem FreeBSD Netmap.

## 4. Matriks Aturan Deteksi Kustom Suricata (`itcorner-local.rules`)

| SID | Pola / Deskripsi Serangan | Mode Aksi Awal | Target Aksi IPS | Lokasi Penempatan |
| --- | --- | --- | --- | --- |
| **1000001** | **Nmap SYN Port Scan to DMZ Web Server:** Lonjakan paket TCP SYN (>20 paket dalam 10 detik) ke `10.10.10.2`. | Alert | Alert / Rate Limit | Edge & Internal OPNsense |
| **1000002** | **Potential SSH Brute-Force on Web Server:** Percobaan koneksi SSH berulang (>5 koneksi dalam 60 detik) ke port 22 `10.10.10.2`. | Alert | Drop / Block Source | Edge & Internal OPNsense |
| **1000003** | **Unauthorized Direct Database Access Attempt:** Percobaan akses langsung ke port PostgreSQL 5432 dari sumber mana pun selain Web Server (`!10.10.10.2 -> 10.10.30.2:5432`). | Alert | **INLINE DROP** | Internal OPNsense (Trunk `em1`) |
| **1000004** | **SQL Injection Attempt in HTTP URI:** Percobaan injeksi SQL dengan pola `UNION ... SELECT` pada URI HTTP menuju Web Server DMZ. | Alert | Drop / WAF Handshake | Edge OPNsense (Parent DMZ) |

## 5. Koordinasi Logging dengan Wazuh SIEM

1. File log Suricata `eve.json` di-generate secara lokal pada instance OPNsense.
2. Wazuh Agent yang terpasang pada router/server membaca berkas `eve.json` menggunakan format log decoder json:
   ```xml
   <localfile>
     <log_format>json</log_format>
     <location>/var/log/suricata/eve.json</location>
   </localfile>
   ```
3. Event dengan level tinggi (seperti deteksi serangan injeksi atau percobaan pembobolan database) langsung memicu alert Wazuh Level >= 10, yang selanjutnya diteruskan ke bot notifikasi Telegram dan dibuatkan tiket insiden pada TheHive.
