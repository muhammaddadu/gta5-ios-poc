#!/usr/bin/env python3
"""Compare a devicectl app-domain inventory to local game files by path and size."""
import argparse
import json
from pathlib import Path


def compare(root, inventory):
    actual = {r['relativePath']: r['metadata']['size'] for r in
              json.loads(inventory.read_text())['result']['files'] if not r['resources'].get('isDirectory')}
    expected = {p.relative_to(root).as_posix(): p.stat().st_size for p in root.rglob('*') if p.is_file()}
    failures = [name for name, size in expected.items() if actual.get(name) != size]
    if failures:
        raise ValueError(f'{len(failures)} missing or wrong-size files; first: {failures[:5]}')
    if not expected:
        raise ValueError('No local files to compare')
    return {'matched_files': len(expected), 'matched_bytes': sum(expected.values()),
            'additional_remote_files': len(set(actual) - set(expected)),
            'scope': 'paths/sizes matched; remote file hashes not read back'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--inventory', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(compare(args.root, args.inventory), indent=2))
