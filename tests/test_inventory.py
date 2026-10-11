import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

spec = importlib.util.spec_from_file_location('inventory', Path(__file__).resolve().parents[1] / 'scripts/verify_inventory.py')
inventory = importlib.util.module_from_spec(spec)
spec.loader.exec_module(inventory)


class InventoryTest(unittest.TestCase):
    def test_complete_manifest_and_corruption(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / 'game'
            root.mkdir()
            sample = root / 'sample.bin'
            sample.write_bytes(b'original synthetic fixture')
            manifest = Path(temp) / 'inventory.json'
            record = {'path': 'mirror/playgta5.com/sample.bin', 'bytes': sample.stat().st_size,
                      'sha256': hashlib.sha256(sample.read_bytes()).hexdigest()}
            manifest.write_text(json.dumps({'files': [record]}))
            self.assertEqual(inventory.verify(root, manifest)['verified_files'], 1)
            sample.write_bytes(b'corrupt! synthetic fixture')
            with self.assertRaises(ValueError):
                inventory.verify(root, manifest)
            sample.unlink()
            with self.assertRaises(ValueError):
                inventory.verify(root, manifest)

    def test_empty_or_escaping_manifest_cannot_pass(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            manifest = root / 'inventory.json'
            for records in [[], [{'path': 'mirror/playgta5.com/../private', 'bytes': 0, 'sha256': ''}]]:
                manifest.write_text(json.dumps({'files': records}))
                with self.assertRaises(ValueError):
                    inventory.verify(root, manifest)
