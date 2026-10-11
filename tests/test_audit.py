import importlib.util
from pathlib import Path
import os
import subprocess
import tempfile
import unittest

spec = importlib.util.spec_from_file_location('audit', Path(__file__).resolve().parents[1] / 'scripts/audit_git.py')
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


class AuditTest(unittest.TestCase):
    def test_force_added_inputs_and_symlinks_rejected(self):
        old = os.getcwd()
        with tempfile.TemporaryDirectory() as temp:
            try:
                os.chdir(temp)
                subprocess.run(['git', 'init', '-q'], check=True)
                Path('README.md').write_text('Original documentation')
                Path('.local').mkdir()
                Path('.local/game.wasm').write_bytes(b'\0asm')
                subprocess.run(['git', 'add', 'README.md', '.local/game.wasm'], check=True)
                self.assertEqual(audit.audit(), ['Not on source allowlist: .local/game.wasm'])
                subprocess.run(['git', 'rm', '--cached', '-q', '.local/game.wasm'], check=True)
                self.assertEqual(audit.audit(), [])
                Path('scripts').mkdir()
                Path('scripts/link.py').symlink_to('../README.md')
                subprocess.run(['git', 'add', 'scripts/link.py'], check=True)
                self.assertEqual(audit.audit(), ['Non-regular file: scripts/link.py'])
            finally:
                os.chdir(old)
