#!/usr/bin/env python3
"""Loopback-only local transport for an authorised browser build. No downloader."""
import argparse
import gzip
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import mimetypes
from pathlib import Path
import re
from urllib.parse import unquote, urlsplit, parse_qs

PROJECT = Path(__file__).resolve().parents[1]
mimetypes.add_type('application/wasm', '.wasm')
mimetypes.add_type('text/javascript', '.js')


class Handler(BaseHTTPRequestHandler):
    def setup(self):
        super().setup()
        self.connection.settimeout(30)

    def reply(self, status, length=0, mime='application/octet-stream', headers=None):
        self.send_response(status)
        self.send_header('Content-Length', str(length))
        self.send_header('Content-Type', mime)
        self.send_header('Cross-Origin-Opener-Policy', 'same-origin')
        self.send_header('Cross-Origin-Embedder-Policy', 'require-corp')
        self.send_header('Cross-Origin-Resource-Policy', 'same-origin')
        self.send_header('Cache-Control', 'no-store')
        for key, value in (headers or {}).items():
            self.send_header(key, value)
        self.end_headers()

    def error(self, status):
        self.reply(status)

    def local_file(self, base, name):
        candidate = (base / name).resolve()
        if not candidate.is_relative_to(base.resolve()) or not candidate.is_file():
            raise FileNotFoundError()
        return candidate

    def do_HEAD(self):
        self.get(head=True)

    def do_GET(self):
        self.get(head=False)

    def get(self, head):
        path = unquote(urlsplit(self.path).path)
        try:
            if path in ('/__support/', '/__support/check.js'):
                file = PROJECT / 'web' / ('index.html' if path.endswith('/') else 'check.js')
            elif path == '/__support/status.json':
                body = json.dumps({'game_present': (self.server.game_root / 'index.html').is_file(),
                                   'engine_path': '/b/8b0b5899ed/game.wasm'}).encode()
                self.reply(200, len(body), 'application/json')
                if not head:
                    self.wfile.write(body)
                return
            else:
                file = self.local_file(self.server.game_root, path.lstrip('/') or 'index.html')
            # Open before headers; symlinks resolving outside the game root are rejected above.
            with file.open('rb') as source:
                size = file.stat().st_size
                start, end, status = 0, size - 1, 200
                headers = {'Accept-Ranges': 'bytes'}
                if 'Range' in self.headers:
                    match = re.fullmatch(r'bytes=(\d*)-(\d*)', self.headers['Range'])
                    if not match or not any(match.groups()):
                        self.reply(416, headers={'Content-Range': f'bytes */{size}'})
                        return
                    a, b = match.groups()
                    start = int(a) if a else max(0, size - int(b))
                    end = min(size - 1, int(b)) if a and b else size - 1
                    if size == 0 or start >= size or end < start:
                        self.reply(416, headers={'Content-Range': f'bytes */{size}'})
                        return
                    status = 206
                    headers['Content-Range'] = f'bytes {start}-{end}/{size}'
                remaining = max(0, end - start + 1)
                self.reply(status, remaining, mimetypes.guess_type(str(file))[0] or 'application/octet-stream', headers)
                if not head:
                    source.seek(start)
                    while remaining:
                        chunk = source.read(min(1024 * 1024, remaining))
                        if not chunk:
                            break
                        self.wfile.write(chunk)
                        remaining -= len(chunk)
        except (OSError, ValueError):
            self.error(404)

    def do_POST(self):
        url = urlsplit(self.path)
        if url.path != '/data/batch':
            self.error(404)
            return
        try:
            length = int(self.headers.get('Content-Length', '-1'))
            if not 0 <= length <= 1024 * 1024:
                self.error(413)
                return
            runs = json.loads(self.rfile.read(length))
            if not isinstance(runs, list) or not 1 <= len(runs) <= 1000:
                raise ValueError()
            selected, total = [], 0
            for name, start, end in runs:
                if not isinstance(name, str) or type(start) is not int or type(end) is not int:
                    raise ValueError()
                if start < 0 or end < start:
                    raise ValueError()
                file = self.local_file(self.server.game_root / 'data', name)
                count = max(0, min(end + 1, file.stat().st_size) - start)
                total += count
                if total > 64 * 1024 * 1024:
                    raise ValueError()
                selected.append((file, start, count))
            chunks = []
            for file, start, count in selected:
                with file.open('rb') as source:
                    source.seek(start)
                    chunks.append(source.read(count))
            body = b''.join(chunks)
            headers = {'X-Run-Lengths': ','.join(str(len(c)) for c in chunks)}
            if parse_qs(url.query).get('gz') == ['1']:
                body = gzip.compress(body, compresslevel=1)
                headers['Content-Encoding'] = 'gzip'
            self.reply(200, len(body), headers=headers)
            self.wfile.write(body)
        except (ValueError, TypeError, OSError):
            self.error(400)


def create_server(root, port=8000):
    server = ThreadingHTTPServer(('127.0.0.1', port), Handler)
    server.game_root = root.resolve()
    return server


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, default=PROJECT / '.local/game')
    parser.add_argument('--port', type=int, default=8000)
    args = parser.parse_args()
    server = create_server(args.root, args.port)
    print(f'Browser checks: http://localhost:{server.server_port}/__support/', flush=True)
    print('Game inputs missing.' if not (args.root / 'index.html').is_file() else 'Game inputs present; gameplay unverified.', flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
