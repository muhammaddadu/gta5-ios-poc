import gzip
import http.client
import importlib.util
import json
from pathlib import Path
import tempfile
import threading
import unittest

spec = importlib.util.spec_from_file_location('serve', Path(__file__).resolve().parents[1] / 'scripts/serve.py')
serve = importlib.util.module_from_spec(spec)
spec.loader.exec_module(serve)


class TransportTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.root = Path(cls.temp.name) / 'game'
        (cls.root / 'data').mkdir(parents=True)
        (cls.root / 'index.html').write_text('<p>Synthetic test page</p>')
        (cls.root / 'data/test.bin').write_bytes(b'0123456789')
        (cls.root / 'empty.bin').write_bytes(b'')
        (Path(cls.temp.name) / 'private.txt').write_text('private')
        (cls.root / 'escape').symlink_to(Path(cls.temp.name) / 'private.txt')
        cls.server = serve.create_server(cls.root, 0)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join()
        cls.temp.cleanup()

    def request(self, method='GET', path='/data/test.bin', body=None, headers=None):
        conn = http.client.HTTPConnection('127.0.0.1', self.server.server_port)
        conn.request(method, path, body=body, headers=headers or {})
        response = conn.getresponse()
        result = response.status, dict(response.getheaders()), response.read()
        conn.close()
        return result

    def test_full_and_isolation(self):
        status, headers, body = self.request()
        self.assertEqual((status, body), (200, b'0123456789'))
        self.assertEqual(headers['Cross-Origin-Opener-Policy'], 'same-origin')
        self.assertEqual(headers['Cross-Origin-Embedder-Policy'], 'require-corp')

    def test_range_variants(self):
        for value, expected in [('bytes=2-4', b'234'), ('bytes=7-', b'789'), ('bytes=-2', b'89'), ('bytes=8-99', b'89')]:
            with self.subTest(value=value):
                status, headers, body = self.request(headers={'Range': value})
                self.assertEqual((status, body), (206, expected))
                self.assertEqual(int(headers['Content-Length']), len(expected))

    def test_bad_ranges(self):
        for value in ['bytes=20-30', 'bytes=5-2', 'bytes=-0', 'bytes=0-1,2-3', 'bytes=-', 'nonsense']:
            self.assertEqual(self.request(headers={'Range': value})[0], 416)
        self.assertEqual(self.request(path='/empty.bin', headers={'Range': 'bytes=0-1'})[0], 416)

    def test_head(self):
        status, headers, body = self.request('HEAD', headers={'Range': 'bytes=1-4'})
        self.assertEqual((status, body, headers['Content-Length']), (206, b'', '4'))

    def test_escape_and_missing(self):
        for path in ['/missing', '/escape', '/%2e%2e/private.txt', '/data/']:
            self.assertEqual(self.request(path=path)[0], 404)

    def test_batch_and_gzip(self):
        body = json.dumps([['test.bin', 1, 3], ['test.bin', 8, 30]])
        status, headers, data = self.request('POST', '/data/batch', body)
        self.assertEqual((status, data, headers['X-Run-Lengths']), (200, b'12389', '3,2'))
        status, headers, data = self.request('POST', '/data/batch?gz=1', body)
        self.assertEqual(gzip.decompress(data), b'12389')
        self.assertEqual(headers['Content-Encoding'], 'gzip')

    def test_batch_rejection(self):
        for body in ['{', '{}', '[1]', '[]', json.dumps([['../private.txt', 0, 2]]), json.dumps([['test.bin', True, 3]]), json.dumps([['test.bin', -1, 3]])]:
            self.assertEqual(self.request('POST', '/data/batch', body)[0], 400)
        self.assertEqual(self.request('POST', '/data/batch', 'x', {'Content-Length': '9999999'})[0], 413)
        self.assertEqual(self.request('POST', '/unknown', '')[0], 404)

    def test_support(self):
        self.assertEqual(self.request(path='/__support/')[0], 200)
        status, _, body = self.request(path='/__support/status.json')
        self.assertTrue(json.loads(body)['game_present'])
