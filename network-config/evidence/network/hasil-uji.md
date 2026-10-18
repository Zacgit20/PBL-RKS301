# Catatan hasil pengujian jaringan dan Suricata IPS

Versi 0.5 - 18 Oktober 2026. Seluruh pengujian lab masih **BELUM DIUJI**. Hasil yang diharapkan adalah kriteria, bukan hasil yang sudah terjadi.

Isi hasil aktual, tanggal, pelaksana, dan tautan bukti pada bagian skenario yang dikerjakan. Gunakan status PASS, FAIL, SEBAGIAN, atau BELUM DIUJI berdasarkan pengamatan. ID adalah penomoran buatan tim.

Target akhirnya adalah IPS. SEC-01/02/03 merupakan persiapan deteksi offline, sedangkan IPS-01 sampai IPS-08 menilai pemblokiran live, trafik normal dan rollback. Alert atau replay saja tidak membuktikan IPS bekerja. Lihat [rencana IPS](../../docs/network/rencana-ips-opnsense.md).

## Daftar skenario

| ID | Skenario | Status |
| --- | --- | --- |
| NET-01 | VLAN20 Management ke gateway | BELUM DIUJI |
| NET-02 | VLAN30 Server ke gateway | BELUM DIUJI |
| NET-03 | VLAN40 SOC ke gateway | BELUM DIUJI |
| NET-04 | VLAN50 Client ke gateway | BELUM DIUJI |
| NET-05 | VLAN60 Testing ke gateway | BELUM DIUJI |
| NET-06 | Transit dua arah | BELUM DIUJI |
| NET-07 | Akses GUI dari Management | BELUM DIUJI |
| NET-08 | Route Web/App ke DB | BELUM DIUJI |
| NET-09 | Client langsung ke DB ditolak | BELUM DIUJI |
| NET-10 | Client ke Web/App HTTPS | BELUM DIUJI |
| NET-11 | Akses HTTPS dari sisi WAN | BELUM DIUJI |
| NET-12 | WAN ke SSH/DB/RDP ditolak | BELUM DIUJI |
| NET-13 | Kali ke zona di luar scope | BELUM DIUJI |
| NET-14 | DNS dan Internet terbatas | BELUM DIUJI |
| SEC-01 | Parser enam custom rules | BELUM DIUJI |
| SEC-02 | Replay fixture positif | BELUM DIUJI |
| SEC-03 | Replay fixture normal | BELUM DIUJI |
| SEC-04 | SQLi/XSS pada jalur live yang terlihat | BELUM DIUJI |
| SOC-01 | Suricata ke Wazuh | BELUM DIUJI |
| SOC-02 | Korelasi login/SSH | BELUM DIUJI |
| IPS-01 | Kesiapan interface dan mode inline | BELUM DIUJI |
| IPS-02 | Aksi efektif drop SID terpilih | BELUM DIUJI |
| IPS-03 | Trafik normal tetap lolos | BELUM DIUJI |
| IPS-04 | Pemblokiran kandidat SQLi plaintext | BELUM DIUJI |
| IPS-05 | Pemblokiran kandidat XSS plaintext | BELUM DIUJI |
| IPS-06 | Tuning login dan SSH | BELUM DIUJI |
| IPS-07 | Logging IPS dan penelusuran SOC | BELUM DIUJI |
| IPS-08 | Persistensi dan rollback IPS | BELUM DIUJI |

## NET-01 - VLAN20 Management ke gateway

| Bagian | Isi |
| --- | --- |
| Sumber / tujuan | Management tag20 -> 10.10.20.1 |
| Hasil yang diharapkan | Respons gateway; capture menunjukkan tag20 |
| Hasil aktual | Belum dicatat |
| Status | BELUM DIUJI |
| Tanggal | Belum dicatat |
| Pelaksana | Belum dicatat |
| Bukti | Belum dilampirkan |

## NET-02 - VLAN30 Server ke gateway

| Bagian | Isi |
| --- | --- |
| Sumber / tujuan | Host tag30 -> 10.10.30.1 |
| Hasil yang diharapkan | Respons gateway; tag30 benar |
| Hasil aktual | Belum dicatat |
| Status | BELUM DIUJI |
| Tanggal | Belum dicatat |
| Pelaksana | Belum dicatat |
| Bukti | Belum dilampirkan |

## NET-03 - VLAN40 SOC ke gateway

| Bagian | Isi |
| --- | --- |
| Sumber / tujuan | Wazuh tag40 -> 10.10.40.1 |
| Hasil yang diharapkan | Respons gateway; tag40 benar |
| Hasil aktual | Belum dicatat |
| Status | BELUM DIUJI |
| Tanggal | Belum dicatat |
| Pelaksana | Belum dicatat |
| Bukti | Belum dilampirkan |

## NET-04 - VLAN50 Client ke gateway

| Bagian | Isi |
| --- | --- |
| Sumber / tujuan | Windows11 tag50 -> 10.10.50.1 |
| Hasil yang diharapkan | Respons gateway; tag50 benar |
| Hasil aktual | Belum dicatat |
| Status | BELUM DIUJI |
| Tanggal | Belum dicatat |
| Pelaksana | Belum dicatat |
| Bukti | Belum dilampirkan |

## NET-05 - VLAN60 Testing ke gateway

| Bagian | Isi |
| --- | --- |
| Sumber / tujuan | Kali tag60 -> 10.10.60.1 |
| Hasil yang diharapkan | Respons gateway; tag60 benar |
| Hasil aktual | Belum dicatat |
| Status | BELUM DIUJI |
| Tanggal | Belum dicatat |
| Pelaksana | Belum dicatat |
| Bukti | Belum dilampirkan |

## NET-06 - Transit dua arah

| Bagian | Isi |
| --- | --- |
| Sumber / tujuan | Edge10.10.1.1 <-> Internal10.10.1.2 |
| Hasil yang diharapkan | Respons dengan rule ICMP diagnostik spesifik bila diperlukan |
| Hasil aktual | Belum dicatat |
| Status | BELUM DIUJI |
| Tanggal | Belum dicatat |
| Pelaksana | Belum dicatat |
| Bukti | Belum dilampirkan |

## NET-07 - Akses GUI dari Management

| Bagian | Isi |
| --- | --- |
| Sumber / tujuan | 10.10.20.2 -> firewall HTTPS |
| Hasil yang diharapkan | Akses sesuai rule admin; catat sertifikat |
| Hasil aktual | Belum dicatat |
| Status | BELUM DIUJI |
| Tanggal | Belum dicatat |
| Pelaksana | Belum dicatat |
| Bukti | Belum dilampirkan |

## NET-08 - Route Web/App ke DB

| Bagian | Isi |
| --- | --- |
| Sumber / tujuan | 10.10.10.2 -> 10.10.30.2 TCP5432 |
| Hasil yang diharapkan | Koneksi akun aplikasi berhasil; source tidak di-NAT antar-zona |
| Hasil aktual | Belum dicatat |
| Status | BELUM DIUJI |
| Tanggal | Belum dicatat |
| Pelaksana | Belum dicatat |
| Bukti | Belum dilampirkan |

## NET-09 - Client langsung ke DB ditolak

| Bagian | Isi |
| --- | --- |
| Sumber / tujuan | 10.10.50.10 -> 10.10.30.2 TCP5432 |
| Hasil yang diharapkan | Ditolak; log firewall sesuai rule |
| Hasil aktual | Belum dicatat |
| Status | BELUM DIUJI |
| Tanggal | Belum dicatat |
| Pelaksana | Belum dicatat |
| Bukti | Belum dilampirkan |

## NET-10 - Client ke Web/App HTTPS

| Bagian | Isi |
| --- | --- |
| Sumber / tujuan | 10.10.50.10 -> 10.10.10.2 TCP443 |
| Hasil yang diharapkan | Layanan HTTPS dapat dijangkau sesuai DNS lab |
| Hasil aktual | Belum dicatat |
| Status | BELUM DIUJI |
| Tanggal | Belum dicatat |
| Pelaksana | Belum dicatat |
| Bukti | Belum dilampirkan |

## NET-11 - Akses HTTPS dari sisi WAN

| Bagian | Isi |
| --- | --- |
| Sumber / tujuan | Penguji di WAN -> alamat WAN Edge TCP443 |
| Hasil yang diharapkan | DNAT hanya menuju Web/App |
| Hasil aktual | Belum dicatat |
| Status | BELUM DIUJI |
| Tanggal | Belum dicatat |
| Pelaksana | Belum dicatat |
| Bukti | Belum dilampirkan |

## NET-12 - WAN ke SSH/DB/RDP ditolak

| Bagian | Isi |
| --- | --- |
| Sumber / tujuan | Penguji WAN -> layanan nonpublik |
| Hasil yang diharapkan | Tidak ada publikasi; ditolak sesuai kebijakan |
| Hasil aktual | Belum dicatat |
| Status | BELUM DIUJI |
| Tanggal | Belum dicatat |
| Pelaksana | Belum dicatat |
| Bukti | Belum dilampirkan |

## NET-13 - Kali ke zona di luar scope

| Bagian | Isi |
| --- | --- |
| Sumber / tujuan | Kali -> target tidak disetujui |
| Hasil yang diharapkan | Ditolak dan tercatat |
| Hasil aktual | Belum dicatat |
| Status | BELUM DIUJI |
| Tanggal | Belum dicatat |
| Pelaksana | Belum dicatat |
| Bukti | Belum dilampirkan |

## NET-14 - DNS dan Internet terbatas

| Bagian | Isi |
| --- | --- |
| Sumber / tujuan | Host disetujui -> resolver/HTTPS tujuan disetujui |
| Hasil yang diharapkan | DNS dan egress berhasil; tujuan lain tetap sesuai kebijakan |
| Hasil aktual | Belum dicatat |
| Status | BELUM DIUJI |
| Tanggal | Belum dicatat |
| Pelaksana | Belum dicatat |
| Bukti | Belum dilampirkan |

## SEC-01 - Parser enam custom rules

| Bagian | Isi |
| --- | --- |
| Sumber / tujuan | suricata -T |
| Hasil yang diharapkan | Exit0 dan 6 SID dimuat; simpan versi/log |
| Hasil aktual | Belum dicatat |
| Status | BELUM DIUJI |
| Tanggal | Belum dicatat |
| Pelaksana | Belum dicatat |
| Bukti | Belum dilampirkan |

## SEC-02 - Replay fixture positif

| Bagian | Isi |
| --- | --- |
| Sumber / tujuan | positive.pcap offline |
| Hasil yang diharapkan | SID1003001 sampai1003006 terlihat; bukan bukti lab live |
| Hasil aktual | Belum dicatat |
| Status | BELUM DIUJI |
| Tanggal | Belum dicatat |
| Pelaksana | Belum dicatat |
| Bukti | Belum dilampirkan |

## SEC-03 - Replay fixture normal

| Bagian | Isi |
| --- | --- |
| Sumber / tujuan | negative.pcap offline |
| Hasil yang diharapkan | Tidak ada alert SID paket |
| Hasil aktual | Belum dicatat |
| Status | BELUM DIUJI |
| Tanggal | Belum dicatat |
| Pelaksana | Belum dicatat |
| Bukti | Belum dilampirkan |

## SEC-04 - SQLi/XSS pada jalur live yang terlihat

| Bagian | Isi |
| --- | --- |
| Sumber / tujuan | HTTP lab terbatas atau WAF HTTPS |
| Hasil yang diharapkan | Event sesuai sumber; jangan klaim dekripsi TLS |
| Hasil aktual | Belum dicatat |
| Status | BELUM DIUJI |
| Tanggal | Belum dicatat |
| Pelaksana | Belum dicatat |
| Bukti | Belum dilampirkan |

## SOC-01 - Suricata ke Wazuh

| Bagian | Isi |
| --- | --- |
| Sumber / tujuan | EVE alert -> collector disepakati |
| Hasil yang diharapkan | Signature ID dan waktu dapat ditelusuri di Wazuh |
| Hasil aktual | Belum dicatat |
| Status | BELUM DIUJI |
| Tanggal | Belum dicatat |
| Pelaksana | Belum dicatat |
| Bukti | Belum dilampirkan |

## SOC-02 - Korelasi login/SSH

| Bagian | Isi |
| --- | --- |
| Sumber / tujuan | Request/koneksi burst + log auth host/aplikasi |
| Hasil yang diharapkan | Kesimpulan gagal login didukung log autentikasi |
| Hasil aktual | Belum dicatat |
| Status | BELUM DIUJI |
| Tanggal | Belum dicatat |
| Pelaksana | Belum dicatat |
| Bukti | Belum dilampirkan |

## IPS-01 - Kesiapan interface dan mode inline

| Bagian | Isi |
| --- | --- |
| Sumber / tujuan | Console dan konfigurasi Edge/Internal |
| Hasil yang diharapkan | NIC/driver, parent, offload, VLAN dan mode inline dicatat; jalur normal dan akses pemulihan tersedia. |
| Mode / sensor / interface | Belum dicatat |
| SID / rev / aksi efektif | Belum dicatat |
| Log lokal / capture / hasil endpoint | Belum dicatat |
| Trafik normal / false positive | Belum dicatat |
| Resource / rollback | Belum dicatat |
| Hasil aktual | Belum dicatat |
| Status | BELUM DIUJI |
| Tanggal | Belum dicatat |
| Pelaksana | Belum dicatat |
| Bukti | Belum dilampirkan |

## IPS-02 - Aksi efektif drop SID terpilih

| Bagian | Isi |
| --- | --- |
| Sumber / tujuan | SID kandidat pada satu sensor uji |
| Hasil yang diharapkan | SID/rev dimuat dan aksi efektif drop terbukti pada konfigurasi engine; tidak ada override yang tidak diketahui. |
| Mode / sensor / interface | Belum dicatat |
| SID / rev / aksi efektif | Belum dicatat |
| Log lokal / capture / hasil endpoint | Belum dicatat |
| Trafik normal / false positive | Belum dicatat |
| Resource / rollback | Belum dicatat |
| Hasil aktual | Belum dicatat |
| Status | BELUM DIUJI |
| Tanggal | Belum dicatat |
| Pelaksana | Belum dicatat |
| Bukti | Belum dilampirkan |

## IPS-03 - Trafik normal tetap lolos

| Bagian | Isi |
| --- | --- |
| Sumber / tujuan | Kali ke endpoint HTTP lab yang disetujui |
| Hasil yang diharapkan | Request normal pada jalur/port uji yang sama mencapai endpoint; firewall dan WAF tidak menutupi hasil IPS. |
| Mode / sensor / interface | Belum dicatat |
| SID / rev / aksi efektif | Belum dicatat |
| Log lokal / capture / hasil endpoint | Belum dicatat |
| Trafik normal / false positive | Belum dicatat |
| Resource / rollback | Belum dicatat |
| Hasil aktual | Belum dicatat |
| Status | BELUM DIUJI |
| Tanggal | Belum dicatat |
| Pelaksana | Belum dicatat |
| Bukti | Belum dilampirkan |

## IPS-04 - Pemblokiran kandidat SQLi plaintext

| Bagian | Isi |
| --- | --- |
| Sumber / tujuan | Endpoint HTTP lab; SID 1003001 atau 1003003 yang dipilih |
| Hasil yang diharapkan | Log lokal, capture dan endpoint menunjukkan payload yang cocok diblokir Suricata IPS; bukan hanya alert/timeout. |
| Mode / sensor / interface | Belum dicatat |
| SID / rev / aksi efektif | Belum dicatat |
| Log lokal / capture / hasil endpoint | Belum dicatat |
| Trafik normal / false positive | Belum dicatat |
| Resource / rollback | Belum dicatat |
| Hasil aktual | Belum dicatat |
| Status | BELUM DIUJI |
| Tanggal | Belum dicatat |
| Pelaksana | Belum dicatat |
| Bukti | Belum dilampirkan |

## IPS-05 - Pemblokiran kandidat XSS plaintext

| Bagian | Isi |
| --- | --- |
| Sumber / tujuan | Endpoint HTTP lab; SID 1003002 atau 1003004 yang dipilih |
| Hasil yang diharapkan | Payload uji yang cocok diblokir dan request normal pembanding tetap lolos; tidak ada klaim dekripsi HTTPS. |
| Mode / sensor / interface | Belum dicatat |
| SID / rev / aksi efektif | Belum dicatat |
| Log lokal / capture / hasil endpoint | Belum dicatat |
| Trafik normal / false positive | Belum dicatat |
| Resource / rollback | Belum dicatat |
| Hasil aktual | Belum dicatat |
| Status | BELUM DIUJI |
| Tanggal | Belum dicatat |
| Pelaksana | Belum dicatat |
| Bukti | Belum dilampirkan |

## IPS-06 - Tuning login dan SSH

| Bagian | Isi |
| --- | --- |
| Sumber / tujuan | SID 1003005/1003006 dan log autentikasi |
| Hasil yang diharapkan | Keduanya tetap alert pada rancangan awal; aktivitas sah dibandingkan dan kesimpulan gagal login didukung log auth. |
| Mode / sensor / interface | Belum dicatat |
| SID / rev / aksi efektif | Belum dicatat |
| Log lokal / capture / hasil endpoint | Belum dicatat |
| Trafik normal / false positive | Belum dicatat |
| Resource / rollback | Belum dicatat |
| Hasil aktual | Belum dicatat |
| Status | BELUM DIUJI |
| Tanggal | Belum dicatat |
| Pelaksana | Belum dicatat |
| Bukti | Belum dilampirkan |

## IPS-07 - Logging IPS dan penelusuran SOC

| Bagian | Isi |
| --- | --- |
| Sumber / tujuan | Log lokal firewall dan alert yang diterima Wazuh |
| Hasil yang diharapkan | SID/waktu/sensor/flow dapat ditelusuri; bukti drop lokal disimpan; raw drop tidak diasumsikan otomatis ikut EVE syslog. |
| Mode / sensor / interface | Belum dicatat |
| SID / rev / aksi efektif | Belum dicatat |
| Log lokal / capture / hasil endpoint | Belum dicatat |
| Trafik normal / false positive | Belum dicatat |
| Resource / rollback | Belum dicatat |
| Hasil aktual | Belum dicatat |
| Status | BELUM DIUJI |
| Tanggal | Belum dicatat |
| Pelaksana | Belum dicatat |
| Bukti | Belum dilampirkan |

## IPS-08 - Persistensi dan rollback IPS

| Bagian | Isi |
| --- | --- |
| Sumber / tujuan | Apply/restart terkontrol dan pengembalian SID uji ke alert |
| Hasil yang diharapkan | Konfigurasi bertahan sesuai target; rollback memulihkan trafik normal; akses console tetap tersedia dan resource dicatat. |
| Mode / sensor / interface | Belum dicatat |
| SID / rev / aksi efektif | Belum dicatat |
| Log lokal / capture / hasil endpoint | Belum dicatat |
| Trafik normal / false positive | Belum dicatat |
| Resource / rollback | Belum dicatat |
| Hasil aktual | Belum dicatat |
| Status | BELUM DIUJI |
| Tanggal | Belum dicatat |
| Pelaksana | Belum dicatat |
| Bukti | Belum dilampirkan |

IPS-06 memerlukan profil yang menyalakan Bastion bila SSH diuji. P7 hanya menyalakan VM untuk skenario HTTP IPS dan logging Wazuh; SOC-IR/DC/Bastion/Management mati. Sesuaikan profil dan aturan akses sebelum uji yang memerlukan komponen tersebut. Jangan menyalin hasil replay sebagai bukti drop live.
