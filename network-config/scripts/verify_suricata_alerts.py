"""Validate local Suricata EVE output against synthetic fixture expectations."""
from pathlib import Path
import argparse
import collections
import json

ROOT = Path(__file__).resolve().parents[1]

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--case',required=True,choices=['positive','negative'])
    parser.add_argument('--eve',required=True,type=Path)
    args = parser.parse_args()
    manifest = json.loads((ROOT/'tests/suricata/expected.json').read_text(encoding='utf-8'))
    expected = set(manifest[args.case]['expected_sids'])
    seen = collections.Counter()
    events = 0
    for line_number,line in enumerate(args.eve.read_text(encoding='utf-8').splitlines(),1):
        if not line.strip():
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError as exc:
            raise SystemExit(f'FAIL: EVE bukan JSON valid pada baris {line_number}: {exc}')
        events += 1
        if event.get('event_type') == 'alert':
            sid = event.get('alert',{}).get('signature_id')
            if isinstance(sid,int) and 1003001 <= sid <= 1003006:
                seen[sid] += 1
    if events == 0:
        raise SystemExit('FAIL: EVE kosong; belum membuktikan engine memproses fixture. Aktifkan EVE flow.')
    missing, unexpected = expected-set(seen), set(seen)-expected
    result = dict(case=args.case, status='PASS' if not missing and not unexpected else 'FAIL',
                  events=events,counts=dict(seen),missing=sorted(missing),unexpected=sorted(unexpected))
    print(json.dumps(result,indent=2))
    raise SystemExit(0 if result['status']=='PASS' else 1)

if __name__ == '__main__':
    main()
