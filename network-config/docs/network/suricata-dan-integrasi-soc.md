# Rules Suricata dan koordinasi SOC

Versi 0.2 - 18 Oktober 2026. Rules dalam paket adalah kandidat IDS alert-only. Belum dimuat pada engine Suricata, belum dipasang di OPNsense, dan belum lulus uji lab.

## Batas deteksi yang perlu disepakati

Sensor pada trafik HTTPS tidak melihat URL/body yang terenkripsi. Rules HTTP di paket memerlukan titik observasi plaintext yang nyata. Gunakan replay PCAP sintetis atau endpoint HTTP khusus lab yang dibatasi sumber Kali; jangan membuka HTTP publik atau mematikan HTTPS untuk demo. Jika plaintext hanya ada pada loopback/container host, sensor Edge tidak otomatis melihatnya. Untuk SQLi/XSS ke layanan HTTPS, tim SOC harus mengumpulkan log ModSecurity/WAF dari Web/App.

SSH terenkripsi dan banyak percobaan password dapat berlangsung dalam satu koneksi. Rule SYN burst hanya petunjuk lonjakan koneksi; cocokkan kegagalan autentikasi dari log SSH host/Wazuh. Rule POST /login menghitung request, bukan hasil login gagal. Jangan menulis evidence “brute force terkonfirmasi” hanya karena dua rule tersebut berbunyi.

| SID | Deteksi kandidat | Bukti tambahan yang diperlukan |
|---:|---|---|
| 1003001 | UNION diikuti whitespace dan SELECT pada URI HTTP ternormalisasi | Request dan alert; bukan semua pola SQLi |
| 1003002 | Awalan tag script pada URI HTTP | Request dan alert; tidak mencakup seluruh XSS |
| 1003003 | UNION SELECT pada body request yang terlihat | Parser body aktif; form URL-encoded tidak otomatis didekode semantik |
| 1003004 | Awalan tag script pada body yang terlihat | Uji JSON/plaintext; encoded entity dapat lolos |
| 1003005 | POST /login berulang, threshold 6 match per 60 detik per sumber | Log aplikasi untuk status sukses/gagal; NAT/proxy dapat menggabungkan sumber |
| 1003006 | SYN menuju Bastion TCP22 berulang, threshold 6 match per 60 detik per sumber | Log SSH; retransmission bisa menaikkan hitungan |

Fixture positif memakai 8 request login dan 8 SYN dalam rentang tersebut agar melewati batas threshold. Fixture negatif memakai pencarian biasa, dua POST login, dan dua SYN. Jumlah persis alert perlu diamati pada versi engine aktual, bukan diasumsikan dari nama rule. Tuning dilakukan setelah hasil normal/serangan terkontrol dibandingkan.

## Urutan pemasangan dan uji

1. Catat versi OPNsense dan `suricata -V`. Backup firewall dan catat ruleset yang sudah aktif.
2. Jalankan `suricata -T` dan replay offline pada sistem yang memiliki Suricata, mengikuti `tests/suricata/README.md`.
3. Pastikan keenam SID tidak bentrok. Mulai dalam mode IDS, bukan mengubah semua alert menjadi drop.
4. Tentukan interface capture dari jalur paket nyata. Untuk trafik bertag dan mode IPS netmap, panduan OPNsense mengarahkan pemilihan parent; validasi driver/offload lebih dahulu. Jangan mengaktifkan parent dan child sekaligus tanpa mengevaluasi duplikasi event.
5. Di OPNsense periksa Services > Intrusion Detection. UI User defined hanya mendukung sebagian rule; jangan menganggap ada tombol impor file .rules penuh tanpa melihat versi lab.
6. Untuk rules custom penuh, gunakan mekanisme ruleset/plugin yang didukung versi tersebut. Template source OPNsense saat riset memiliki include conf.d, tetapi itu bukan verifikasi versi lab. Jika memakai custom YAML/template, simpan daftar rule aktif dan tambahkan file lokal tanpa menimpa ruleset lain. Periksa hasil render dan ulangi -T sebelum reload. Jangan hanya menyalin file ke suatu folder lalu menganggapnya sudah dimuat.
7. Setelah metode persistensi dipilih, catat lokasi file, konfigurasi pemuatan, hash, enam SID yang dimuat, hasil -T, dan metode rollback. Verifikasi tetap dimuat setelah Apply/restart.
8. Jalankan skenario terbatas; ambil alert dan baseline normal. Ubah rev bila isi rule berubah. Uji kembali sebelum IPS/drop.

Metode pemuatan persisten untuk OPNsense 26.7 masih perlu diperiksa pada VM aktual. Paket ini tidak menimpa YAML hasil generate, tidak mengubah template vendor, dan tidak menjanjikan file .rules sudah aktif setelah sekadar di-upload. Ini pekerjaan integrasi yang tersisa, bukan hasil pengujian.

## Pengiriman ke anggota SOC

| Sumber | Data | Tujuan koordinasi |
|---|---|---|
| Suricata Edge/Internal | EVE alert: timestamp, signature_id, signature, severity, src/dest IP/port, proto, flow_id bila tersedia | Wazuh 10.10.40.2 |
| Web/App WAF | ModSecurity audit log; path aktual ditentukan konfigurasi Nginx/ModSecurity | Wazuh 10.10.40.2 |
| Bastion | Log autentikasi SSH, lokasi sesuai OS | Wazuh 10.10.40.2 |
| Aplikasi | Keberhasilan/kegagalan login, tanpa password/token | Wazuh 10.10.40.2 |

OPNsense menyediakan EVE syslog output dan target logging. Gunakan filter aplikasi suricata sesuai dokumentasi, lalu sepakati listener/transport dengan SOC. Path EVE pada template source adalah /var/log/suricata/eve.json; cek konfigurasi hasil generate pada lab sebelum menetapkan path monitoring. WAF `/var/log/modsec_audit.log` dari arahan tugas adalah calon path, bukan bukti file sudah ada.

Nur Arsyika Juana menangani Threat Matrix dan kesiapan SOC berdasarkan arahan tugas yang dibagikan. Tim Network menyediakan sumber event dan evidence; tim SOC memverifikasi decoder/rule Wazuh, notifikasi Telegram, serta case TheHive 10.10.40.3. Token Telegram, API key, dan private key dikelola terpisah.

## Acceptance criteria

- Enam SID lulus parser engine yang benar, tidak ada rule gagal dimuat.
- Replay positif memunculkan SID yang diharapkan; replay negatif tidak memicu SID paket.
- Uji live membuktikan sensor melihat jalur yang diuji, bukan hanya fixture offline.
- Event EVE yang sama dapat ditelusuri ke Wazuh; tim SOC mencatat alert ID/case ID jika diteruskan.
- Laporan membedakan pola berbahaya, lonjakan request/koneksi, dan kegagalan autentikasi yang terkonfirmasi.

## Sumber

- https://docs.opnsense.org/manual/ips.html
- https://docs.suricata.io/en/suricata-7.0.10/rules/http-keywords.html
- https://docs.suricata.io/en/suricata-7.0.10/rules/thresholding.html
- https://docs.suricata.io/en/suricata-7.0.10/rules/ssh-keywords.html
- https://docs.suricata.io/en/suricata-7.0.10/command-line-options.html
- https://raw.githubusercontent.com/opnsense/core/master/src/opnsense/service/templates/OPNsense/IDS/suricata.yaml
