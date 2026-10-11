#!/usr/bin/env python3
"""Local POC acquisition; uses reviewed pinned upstream extractor, never commits inputs."""
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
LOCAL = ROOT / '.local'


def main():
    lock = json.loads((ROOT / 'upstreams.json').read_text())
    helper = LOCAL / 'download_game.py'
    actual = hashlib.sha256(helper.read_bytes()).hexdigest()
    if actual != lock['browser_reference']['downloader_sha256']:
        raise ValueError('Upstream downloader differs from reviewed source')
    spec = importlib.util.spec_from_file_location('reviewed_downloader', helper)
    upstream = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(upstream)
    manifest = json.loads((LOCAL / 'download-manifest.json').read_text())
    records = json.loads((LOCAL / 'file-inventory.json').read_text())['files']
    names = [r['path'] for r in records]
    if len(names) != len(set(names)):
        raise ValueError('Inventory has overlapping paths')
    cache = LOCAL / '.downloads'
    cache.mkdir(exist_ok=True)
    receipts = LOCAL / '.installed-parts'
    receipts.mkdir(exist_ok=True)
    expected_url = 'https://github.com/alihammoud21/playgta5/releases/download/full-game-v1/'

    def part_task(part):
        name = part['name']
        if Path(name).name != name or not part['url'] == expected_url + name:
            raise ValueError('Unexpected release URL or filename')
        selected = [r for r in records if r['part'] == name]
        receipt = receipts / (name + '.sha256')
        game = [r for r in selected if upstream.payload(r['path'], windows=False)]
        if receipt.is_file() and receipt.read_text().strip() == part['sha256'] and all(
            upstream.target_path(LOCAL, r['path']).is_file() and upstream.target_path(LOCAL, r['path']).stat().st_size == r['bytes'] for r in game):
            print('Already installed:', name, flush=True)
            return
        archive = cache / name
        partial = cache / (name + '.partial')
        if not archive.exists():
            print('Downloading:', name, flush=True)
            subprocess.run(['curl', '--silent', '--show-error', '--fail', '--location',
                            '--retry', '4', '--continue-at', '-', '--output', str(partial), part['url']], check=True)
            if partial.stat().st_size != part['bytes'] or upstream.digest(partial) != part['sha256']:
                raise ValueError('Archive checksum mismatch: ' + name)
            partial.replace(archive)
        if archive.stat().st_size != part['bytes'] or upstream.digest(archive) != part['sha256']:
            raise ValueError('Archive checksum mismatch: ' + name)
        print('Extracting:', name, flush=True)
        upstream.extract_payload(archive, LOCAL, selected, windows=False)
        receipt.write_text(part['sha256'])
        print('Installed:', name, flush=True)
        # Keep verified archives local for reproducibility; no deletion needed.

    # Distinct inventory paths permit parallel extraction. Disk preflight covers all archives + files.
    import shutil
    required = sum(p['bytes'] for p in manifest['parts']) + sum(r['bytes'] for r in records if upstream.payload(r['path'], windows=False))
    if shutil.disk_usage(LOCAL).free < required + 1024 ** 3:
        raise ValueError('Need free space for all archive + extracted bytes (conservative restart check)')
    with ThreadPoolExecutor(max_workers=4) as pool:
        futures = [pool.submit(part_task, p) for p in manifest['parts']]
        for future in as_completed(futures):
            future.result()
    print('Complete. Run verify_inventory.py and verify_assets.py before gameplay.', flush=True)


if __name__ == '__main__':
    main()
