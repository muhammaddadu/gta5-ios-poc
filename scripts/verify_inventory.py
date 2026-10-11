#!/usr/bin/env python3
"""Hash every game file against a locally supplied upstream inventory."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

PROJECT = Path(__file__).resolve().parents[1]
PREFIX = 'mirror/playgta5.com/'


def verify(root, inventory):
    records = json.loads(inventory.read_text())['files']
    failures, count, total = [], 0, 0
    for record in records:
        if not record['path'].startswith(PREFIX):
            continue
        relative = Path(record['path'][len(PREFIX):])
        file = (root / relative).resolve()
        if relative.is_absolute() or '..' in relative.parts or not file.is_relative_to(root.resolve()):
            raise ValueError('Unsafe inventory path')
        try:
            if file.stat().st_size != record['bytes']:
                raise ValueError('size mismatch')
            with file.open('rb') as source:
                digest = hashlib.file_digest(source, 'sha256').hexdigest()
            if digest != record['sha256']:
                raise ValueError('hash mismatch')
            count += 1
            total += record['bytes']
        except (OSError, ValueError) as error:
            failures.append(f'{relative}: {error}')
        if count and count % 1000 == 0:
            print(f'Verified {count} files', flush=True)
    if not count:
        failures.append('No game records verified')
    if failures:
        raise ValueError('\n'.join(failures[:20]) + f'\nFailures: {len(failures)}')
    return {'verified_files': count, 'verified_bytes': total,
            'note': 'Matches supplied inventory; not a safety, permission or gameplay certification'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, default=PROJECT / '.local/game')
    parser.add_argument('--inventory', type=Path, default=PROJECT / '.local/file-inventory.json')
    args = parser.parse_args()
    try:
        print(json.dumps(verify(args.root.resolve(), args.inventory), indent=2))
    except (OSError, ValueError) as error:
        print(error, file=sys.stderr)
        sys.exit(1)
