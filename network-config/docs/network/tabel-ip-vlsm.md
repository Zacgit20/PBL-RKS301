# Tabel IP dan VLSM ITCorner.id

**Versi:** 0.4 - 18 Oktober 2026  
**Status:** baseline target RPP Final; bukan hasil discovery perangkat.

Nama zona dicantumkan pada pembagian subnet, daftar host, dan daftar interface. Alamat yang sudah terpasang di lab tetap perlu diverifikasi sesuai dokumentasi konfigurasi.

## 1. Pembagian zona, VLAN, dan gateway

| Nama zona | Fungsi zona | VLAN | Subnet / prefix | Gateway / router |
| --- | --- | --- | --- | --- |
| Transit Antar-Firewall | Penghubung Edge dan Internal Firewall. | - | 10.10.1.0/30 | Edge 10.10.1.1; Internal 10.10.1.2 |
| DMZ | Layanan publik Web/App dan Bastion Host. | 10 | 10.10.10.0/29 | 10.10.10.1 |
| DevOps & Management | Administrasi dan GitHub Actions self-hosted runner. | 20 | 10.10.20.0/29 | 10.10.20.1 |
| Server/Data | Database, backup, serta AD DS/DNS. | 30 | 10.10.30.0/29 | 10.10.30.1 |
| SOC | Pemantauan keamanan dan penanganan insiden. | 40 | 10.10.40.0/29 | 10.10.40.1 |
| Internal Client | Endpoint Windows 11 dan Ubuntu Client. | 50 | 10.10.50.0/27 | 10.10.50.1 |
| Security Testing | Kali Linux untuk pengujian terkontrol. | 60 | 10.10.60.0/30 | 10.10.60.1 |
| WireGuard Tunnel | Tunnel administrator; layanan Edge, bukan VM tambahan. | - | 10.10.70.0/29 | 10.10.70.1 |

## 2. Perhitungan VLSM

| Nama zona | Subnet / prefix | Netmask | Rentang host usable | Broadcast | Kapasitas host | Alokasi baseline | Sisa baseline |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Transit Antar-Firewall | 10.10.1.0/30 | 255.255.255.252 | 10.10.1.1 - 10.10.1.2 | 10.10.1.3 | 2 | 2 | 0 |
| DMZ | 10.10.10.0/29 | 255.255.255.248 | 10.10.10.1 - 10.10.10.6 | 10.10.10.7 | 6 | 3 | 3 |
| DevOps & Management | 10.10.20.0/29 | 255.255.255.248 | 10.10.20.1 - 10.10.20.6 | 10.10.20.7 | 6 | 2 | 4 |
| Server/Data | 10.10.30.0/29 | 255.255.255.248 | 10.10.30.1 - 10.10.30.6 | 10.10.30.7 | 6 | 4 | 2 |
| SOC | 10.10.40.0/29 | 255.255.255.248 | 10.10.40.1 - 10.10.40.6 | 10.10.40.7 | 6 | 3 | 3 |
| Internal Client | 10.10.50.0/27 | 255.255.255.224 | 10.10.50.1 - 10.10.50.30 | 10.10.50.31 | 30 | 3 | 27 |
| Security Testing | 10.10.60.0/30 | 255.255.255.252 | 10.10.60.1 - 10.10.60.2 | 10.10.60.3 | 2 | 2 | 0 |
| WireGuard Tunnel | 10.10.70.0/29 | 255.255.255.248 | 10.10.70.1 - 10.10.70.6 | 10.10.70.7 | 6 | 6 | 0 |

Kapasitas host dihitung dengan rumus `2^(32-prefix)-2` untuk subnet pada tabel. Alokasi baseline mencakup gateway/router dan host yang direncanakan, bukan jumlah perangkat yang sudah aktif. Pada WireGuard, lima alamat peer masih berupa cadangan. Subnet Security Testing /30 tepat menampung satu gateway dan satu Kali.

## 3. Daftar IP 13 VM beserta nama zona

| No. VM | Nama VM | Nama zona | VLAN | IP utama / prefix | Gateway | Fungsi | vCPU | RAM (GiB) | Disk (GiB) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 01 | Edge OPNsense | Perimeter / Transit / DMZ | - | 10.10.1.1/30 | Upstream WAN belum diketahui | Router; juga gateway DMZ dan WireGuard | 2 | 4 | 40 |
| 02 | Internal OPNsense | Transit / gateway VLAN internal | - | 10.10.1.2/30 | 10.10.1.1 | Router; gateway VLAN 20 sampai 60 | 2 | 4 | 40 |
| 03 | Web/App | DMZ | 10 | 10.10.10.2/29 | 10.10.10.1 | Nginx; ModSecurity; Flask; Gunicorn; Docker | 2 | 2 | 32 |
| 04 | Bastion | DMZ | 10 | 10.10.10.3/29 | 10.10.10.1 | Jump host; VM terpisah | 1 | 1 | 16 |
| 05 | Management + Runner | DevOps & Management | 20 | 10.10.20.2/29 | 10.10.20.1 | Administrasi; GitHub Actions self-hosted runner | 2 | 2 | 40 |
| 06 | Database | Server/Data | 30 | 10.10.30.2/29 | 10.10.30.1 | PostgreSQL | 2 | 2 | 32 |
| 07 | Backup | Server/Data | 30 | 10.10.30.3/29 | 10.10.30.1 | Restic; SSH/SFTP | 1 | 1 | 64 |
| 08 | Windows Server 2025 | Server/Data | 30 | 10.10.30.4/29 | 10.10.30.1 | AD DS; DNS | 2 | 4 | 64 |
| 09 | Wazuh | SOC | 40 | 10.10.40.2/29 | 10.10.40.1 | Manager; Indexer; Dashboard | 4 | 8 | 80 |
| 10 | SOC-IR | SOC | 40 | 10.10.40.3/29 | 10.10.40.1 | TheHive; Cortex; MISP dalam satu VM | 4 | 12 | 160 |
| 11 | Windows 11 Enterprise | Internal Client | 50 | 10.10.50.10/27 | 10.10.50.1 | Client domain | 2 | 4 | 80 |
| 12 | Ubuntu Client | Internal Client | 50 | 10.10.50.20/27 | 10.10.50.1 | Client Linux | 2 | 2 | 32 |
| 13 | Kali Linux | Security Testing | 60 | 10.10.60.2/30 | 10.10.60.1 | Pengujian sesuai scope | 2 | 2 | 40 |

Untuk Edge dan Internal, IP utama di tabel adalah IP interface Transit. Keduanya memiliki interface gateway lain pada tabel berikut; router tidak dibatasi hanya pada satu zona. Alamat WAN Edge mengikuti upstream lab dan belum diketahui.

**Jumlah target hardware seluruh VM:** 28 vCPU, 48 GiB RAM dan 720 GiB disk virtual. Pada PC 32 GB, jalankan profil bergantian; jangan menyalakan seluruh VM sekaligus. OS, jumlah adapter, dasar alokasi dan daftar VM aktif per profil ada di [spesifikasi VM untuk PC 32 GB](spesifikasi-vm-32gb.md).

## 4. Alamat interface router

| Router | Nama zona / interface | VLAN | Alamat | Keterangan |
| --- | --- | --- | --- | --- |
| Edge | WAN / Upstream | - | Mengikuti upstream lab; belum dicatat | Keluar melalui upstream |
| Edge | Transit Antar-Firewall | - | 10.10.1.1/30 | Ke Internal 10.10.1.2 |
| Edge | DMZ | 10 | 10.10.10.1/29 | Gateway Web/App dan Bastion |
| Edge | WireGuard Tunnel | - | 10.10.70.1/29 | Gateway tunnel administrator |
| Internal | Transit Antar-Firewall | - | 10.10.1.2/30 | Default gateway 10.10.1.1 |
| Internal | DevOps & Management | 20 | 10.10.20.1/29 | Gateway Management/Runner |
| Internal | Server/Data | 30 | 10.10.30.1/29 | Gateway Database, Backup, Windows Server |
| Internal | SOC | 40 | 10.10.40.1/29 | Gateway Wazuh dan SOC-IR |
| Internal | Internal Client | 50 | 10.10.50.1/27 | Gateway Windows 11 dan Ubuntu Client |
| Internal | Security Testing | 60 | 10.10.60.1/30 | Gateway Kali Linux |

## 5. Ringkasan host per zona

| Nama zona | Host / alokasi alamat |
| --- | --- |
| Transit Antar-Firewall | Edge 10.10.1.1; Internal 10.10.1.2 |
| DMZ | Web/App 10.10.10.2; Bastion 10.10.10.3 |
| DevOps & Management | Management + Runner 10.10.20.2 |
| Server/Data | Database 10.10.30.2; Backup 10.10.30.3; Windows Server 10.10.30.4 |
| SOC | Wazuh 10.10.40.2; SOC-IR 10.10.40.3 |
| Internal Client | Windows 11 10.10.50.10; Ubuntu Client 10.10.50.20 |
| Security Testing | Kali Linux 10.10.60.2 |
| WireGuard Tunnel | Edge tunnel 10.10.70.1; peer admin 10.10.70.2-10.10.70.6 dicadangkan |

## 6. Catatan penggunaan

- Gateway klien adalah interface router pada subnetnya, bukan IP Transit. Semua prefix harus diisi sesuai tabel, bukan selalu /24.
- DNS client domain diarahkan ke Windows Server 10.10.30.4 setelah AD DS/DNS siap. Resolver/forwarder firewall dan kebutuhan NTP ditentukan serta diuji terpisah.
- ITCorner.id adalah nama aplikasi; kepemilikan domain publik belum dikonfirmasi. Nama DNS lab seperti itcorner.test dapat disepakati tim.
- Delapan subnet tidak saling overlap. VLAN ID dan alamat subnet adalah dua pengaturan berbeda. Nama LAN Segment tidak otomatis memberi tag VLAN.
- Pada desain guest tagging, Windows Server memakai tag 30 dan Windows 11 tag 50; keberhasilan konektivitas perlu dibuktikan.
- Bastion adalah VM terpisah, runner tetap pada Management, dan TheHive/Cortex/MISP berada pada satu VM SOC-IR. Telegram serta penguji eksternal tidak dihitung sebagai tambahan VM utama.
