"""Build synthetic Ethernet/IPv4/TCP PCAPs locally for Suricata rules verification.
Never sends network traffic. Aligned with RPP Rev.3 ruleset (SID 1000001-1000004).
"""
from pathlib import Path
import struct
import socket
import json

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / 'tests' / 'suricata'
SRC = '10.10.60.2'
WEB = '10.10.10.2'
DB = '10.10.30.2'

def checksum(data):
    if len(data) % 2:
        data += b'\x00'
    value = sum(struct.unpack('!%dH' % (len(data)//2), data))
    while value >> 16:
        value = (value & 0xffff) + (value >> 16)
    return (~value) & 0xffff

def frame(src, dst, sport, dport, seq, ack, flags, payload=b''):
    srcip, dstip = socket.inet_aton(src), socket.inet_aton(dst)
    tcp = struct.pack('!HHIIBBHHH', sport, dport, seq, ack, 0x50, flags, 65535, 0, 0)
    pseudo = srcip + dstip + struct.pack('!BBH', 0, 6, len(tcp)+len(payload))
    tcp_sum = checksum(pseudo+tcp+payload)
    tcp = struct.pack('!HHIIBBHHH', sport, dport, seq, ack, 0x50, flags, 65535, tcp_sum, 0)
    ip = struct.pack('!BBHHHBBH4s4s', 0x45, 0, 20+len(tcp)+len(payload), 1, 0, 64, 6, 0, srcip, dstip)
    ip = struct.pack('!BBHHHBBH4s4s', 0x45, 0, 20+len(tcp)+len(payload), 1, 0, 64, 6, checksum(ip), srcip, dstip)
    eth = bytes.fromhex('0200000000020200000000010800')
    return eth + ip + tcp + payload

def http_request(method, uri, body=b'', content_type='application/json'):
    headers = f'{method} {uri} HTTP/1.1\r\nHost: itcorner.test\r\nConnection: close\r\n'
    if method == 'POST':
        headers += f'Content-Type: {content_type}\r\nContent-Length: {len(body)}\r\n'
    return headers.encode('ascii') + b'\r\n' + body

def transaction(number, request):
    sport = 40000 + number
    a = 1000 + number*10000
    b = 9000 + number*10000
    response = b'HTTP/1.1 200 OK\r\nContent-Length: 2\r\nConnection: close\r\n\r\nOK'
    ac, bs = a+1+len(request), b+1+len(response)
    return [
        frame(SRC, WEB, sport, 8080, a, 0, 2),
        frame(WEB, SRC, 8080, sport, b, a+1, 0x12),
        frame(SRC, WEB, sport, 8080, a+1, b+1, 0x10),
        frame(SRC, WEB, sport, 8080, a+1, b+1, 0x18, request),
        frame(WEB, SRC, 8080, sport, b+1, ac, 0x10),
        frame(WEB, SRC, 8080, sport, b+1, ac, 0x18, response),
        frame(SRC, WEB, sport, 8080, ac, bs, 0x10),
        frame(SRC, WEB, sport, 8080, ac, bs, 0x11),
        frame(WEB, SRC, 8080, sport, bs, ac+1, 0x11),
        frame(SRC, WEB, sport, 8080, ac+1, bs+1, 0x10),
    ]

def save_pcap(name, packets):
    p = DEST / name
    with p.open('wb') as f:
        f.write(struct.pack('<IHHIIII', 0xa1b2c3d4, 2, 4, 0, 0, 65535, 1))
        for i, packet in enumerate(packets):
            usec = i * 20000
            f.write(struct.pack('<IIII', 1792281600+usec//1000000, usec%1000000, len(packet), len(packet)))
            f.write(packet)

def validate_pcap(p):
    """Validate record lengths, IPv4 and TCP checksums; not Suricata detection."""
    data = p.read_bytes()
    magic, major, minor, _, _, snaplen, link = struct.unpack('<IHHIIII', data[:24])
    assert (magic,major,minor,link) == (0xa1b2c3d4,2,4,1)
    offset, count = 24, 0
    while offset < len(data):
        _, usec, captured, original = struct.unpack('<IIII', data[offset:offset+16])
        offset += 16
        packet = data[offset:offset+captured]
        offset += captured
        assert len(packet) == captured == original and usec < 1000000
        assert packet[12:14] == b'\x08\x00'
        ip = packet[14:34]
        assert checksum(ip) == 0 and ip[9] == 6
        length = struct.unpack('!H', ip[2:4])[0]
        assert len(packet) == 14+length
        segment = packet[34:14+length]
        pseudo = ip[12:20]+struct.pack('!BBH', 0, 6, len(segment))
        assert checksum(pseudo+segment) == 0
        count += 1
    assert offset == len(data)
    return count

def main():
    DEST.mkdir(parents=True, exist_ok=True)
    
    # 1. Positive Fixtures:
    # SID 1000001: SYN Scan to Web DMZ (25 SYN packets within 10s threshold count 20)
    syn_scan = [frame(SRC, WEB, 45000+i, 80+i, 100000+i*100, 0, 2) for i in range(25)]
    
    # SID 1000002: SSH Brute-Force to Web DMZ port 22 (8 SYN packets threshold count 5)
    ssh_burst = [frame(SRC, WEB, 50000+i, 22, 200000+i*100, 0, 2) for i in range(8)]
    
    # SID 1000003: Direct DB Access attempt from unauthorized IP (10.10.60.2 -> 10.10.30.2:5432)
    db_attempt = [frame(SRC, DB, 55000+i, 5432, 300000+i*100, 0, 2) for i in range(3)]
    
    # SID 1000004: SQL Injection attempt in HTTP URI (UNION ... SELECT)
    sqli_req = http_request('GET', '/products?search=item%20UNION%20SELECT%20username,password%20FROM%20users')
    sqli_tx = transaction(1, sqli_req)
    
    positive = syn_scan + ssh_burst + db_attempt + sqli_tx
    
    # 2. Negative Fixtures (Normal Traffic):
    # Few SYN packets (< 20 threshold)
    normal_syn = [frame(SRC, WEB, 46000+i, 80, 400000+i*100, 0, 2) for i in range(5)]
    # Few SSH packets (< 5 threshold)
    normal_ssh = [frame(SRC, WEB, 51000+i, 22, 500000+i*100, 0, 2) for i in range(2)]
    # Normal HTTP requests
    normal_http_req = http_request('GET', '/products?search=monitor')
    normal_http_tx = transaction(101, normal_http_req)
    
    negative = normal_syn + normal_ssh + normal_http_tx
    
    save_pcap('positive.pcap', positive)
    save_pcap('negative.pcap', negative)
    counts = {name: validate_pcap(DEST/name) for name in ('positive.pcap', 'negative.pcap')}
    
    manifest = {
        'kind': 'synthetic offline fixtures; not lab evidence',
        'engine_test_status': 'NOT_RUN',
        'positive': {
            'file': 'positive.pcap',
            'expected_sids': [1000001, 1000002, 1000003, 1000004],
            'packet_count': counts['positive.pcap']
        },
        'negative': {
            'file': 'negative.pcap',
            'expected_sids': [],
            'packet_count': counts['negative.pcap']
        },
        'scope': 'No sockets opened. Synthetic PCAP for RPP Rev.3 ruleset verification (SID 1000001-1000004).'
    }
    (DEST / 'expected.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'fixture_checksums': 'PASS', 'packets': counts, 'suricata_replay': 'NOT_RUN'}))

if __name__ == '__main__':
    main()
