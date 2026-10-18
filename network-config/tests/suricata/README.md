# Uji offline baseline rules untuk persiapan IPS

Fixture PCAP dibuat lokal dari data sintetis, bukan capture lab dan bukan bukti serangan ke aplikasi. Tidak ada paket yang dikirim ke jaringan. Positive berisi empat pola HTTP, delapan POST login, dan delapan SYN SSH. Negative berisi pencarian biasa, dua POST login, dan dua SYN SSH. Header IPv4 dan checksum TCP diperiksa saat fixture dibentuk; engine Suricata belum dijalankan.

## Persiapan

Gunakan mesin uji dengan Suricata terpasang. Catat `suricata -V`. Perintah berikut dijalankan dari root paket pada shell Linux/FreeBSD. Python3 hanya diperlukan untuk membangun fixture dan membaca hasil. Fixture yang sudah dibangun ikut disertakan.

```sh
python3 scripts/build_suricata_fixtures.py
mkdir -p evidence/network/offline-parser evidence/network/offline-positive evidence/network/offline-negative
suricata -T -c tests/suricata/offline-test.yaml -S config/suricata/itcorner-local.rules --init-errors-fatal -l evidence/network/offline-parser
```

Lanjut hanya bila exit code 0 dan semua 6 SID dimuat. YAML offline adalah kandidat konfigurasi minimal, bukan konfigurasi OPNsense. Jika versi engine membutuhkan pengaturan tambahan, perbaiki pada mesin uji dan simpan versi/log; jangan mengklaim -T sudah lulus dari pemeriksaan teks saja.

## Replay

Gunakan direktori output baru/kosong untuk setiap percobaan agar alert lama tidak ikut dihitung. Jangan menghapus evidence lama; gunakan nama percobaan berikutnya dan sesuaikan argumen `-l`.

```sh
suricata --runmode single -c tests/suricata/offline-test.yaml -S config/suricata/itcorner-local.rules -r tests/suricata/positive.pcap -l evidence/network/offline-positive
python3 scripts/verify_suricata_alerts.py --case positive --eve evidence/network/offline-positive/eve.json

suricata --runmode single -c tests/suricata/offline-test.yaml -S config/suricata/itcorner-local.rules -r tests/suricata/negative.pcap -l evidence/network/offline-negative
python3 scripts/verify_suricata_alerts.py --case negative --eve evidence/network/offline-negative/eve.json
```

Setiap perintah Suricata harus selesai berhasil sebelum hasilnya diperiksa. Verifier menolak EVE kosong/JSON rusak dan membandingkan SID paket, bukan semua alert dari ruleset lain. Ekspektasi positive adalah keenam SID muncul setidaknya sekali; negative tidak memiliki SID paket. Ekspektasi bukan hasil aktual. Simpan console log, versi engine, EVE, dan keluaran verifier.

Keberhasilan replay tidak membuktikan pemuatan persisten di OPNsense, penerusan VLAN, akses HTTPS, atau integrasi Wazuh. Uji live dan visibility sensor tetap diperlukan. Tidak ada uji IPS drop dalam fixture ini.

Referensi: https://docs.suricata.io/en/suricata-7.0.10/command-line-options.html

## Hubungan dengan target IPS

Target akhir proyek adalah Suricata IPS, tetapi PCAP dan YAML di folder ini tetap baseline deteksi offline dengan rules alert. Menjalankan replay tidak membuat jalur live inline atau membuktikan payload diblokir. Rencana drop terpilih dan uji live IPS-01 sampai IPS-08 ada di `docs/network/rencana-ips-opnsense.md` dan `evidence/network/hasil-uji.md` relatif root paket.

Keterbatasan verifier yang sudah diketahui: kasus negatif dapat memberi PASS pada JSON biasa/event stats tanpa bukti PCAP diproses. Verifier belum diperbaiki pada revisi dokumentasi ini; jangan gunakan hasilnya sebagai acceptance sebelum perbaikan dan validasi input/proses engine selesai. Munculnya alert offline juga bukan bukti IPS aktif.
