#!/usr/bin/env python3
"""Structural and compatibility checks of user-supplied, authorised local files."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]


def verify(root):
    config = json.loads((ROOT / 'upstreams.json').read_text())['engine']
    build = root / 'b' / config['build']
    missing = [str(p.relative_to(root)) for p in
               [root / 'index.html', build / 'game.wasm', build / 'game.js',
                build / 'shaders' / 'index.json'] if not p.is_file()]
    if not (root / 'data').is_dir() or not any(p.is_file() for p in (root / 'data').rglob('*')):
        missing.append('data/ (nonempty)')
    if missing:
        raise ValueError('Missing: ' + ', '.join(missing))
    wasm = build / 'game.wasm'
    with wasm.open('rb') as source:
        if source.read(8) != b'\x00asm\x01\x00\x00\x00':
            raise ValueError('Invalid WASM header')
        source.seek(0)
        digest = hashlib.file_digest(source, 'sha256').hexdigest()
    if digest != config['sha256']:
        raise ValueError(f'Unsupported engine SHA-256: {digest}')
    return {'engine_sha256': digest, 'build': config['build'],
            'status': 'structural checks passed; full asset integrity and gameplay unverified'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, default=ROOT / '.local/game')
    args = parser.parse_args()
    try:
        print(json.dumps(verify(args.root.resolve()), indent=2))
    except (ValueError, OSError) as error:
        print(str(error), file=sys.stderr)
        sys.exit(1)
