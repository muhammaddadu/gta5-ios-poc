import importlib.util
from pathlib import Path
import tempfile
import unittest

spec = importlib.util.spec_from_file_location('integration', Path(__file__).resolve().parents[1]/'scripts/integrate-glue5.py')
integration = importlib.util.module_from_spec(spec)
spec.loader.exec_module(integration)


class IntegrationTest(unittest.TestCase):
    def test_idempotent_compatibility_and_preserved_fallback(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            fixtures = {
                'crates/glue5-runtime/src/lib.rs': 'pub fn shader_dir(game: &Path) -> PathBuf {\n    game.join("b")\n}\n',
                'crates/glue5/src/paths.rs': 'pub fn user_dir() -> Result<PathBuf> {\n    original_user_dir()\n}\nfn dirs() {\n    dirs.push(docs.join("game"));\n}\n',
                'crates/glue5/src/settings.rs': 'let settings = Settings { low_memory: MOBILE && ram < 7000, };\n',
                'crates/glue5/src/lib.rs': 'show_error("Glue 5");\n',
            }
            for name,text in fixtures.items():
                p=root/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(text)
            integration.patch(root)
            first={name:(root/name).read_text() for name in fixtures}
            integration.patch(root)
            self.assertEqual(first,{name:(root/name).read_text() for name in fixtures})
            self.assertIn('legacy.join("index.json").is_file()',first['crates/glue5-runtime/src/lib.rs'])
            self.assertIn('game.join("b")',first['crates/glue5-runtime/src/lib.rs'])
            self.assertIn('docs.join("userdata")',first['crates/glue5/src/paths.rs'])
            self.assertIn('dirs.push(docs.to_path_buf())',first['crates/glue5/src/paths.rs'])
            self.assertIn('cfg!(target_os = "ios")',first['crates/glue5/src/settings.rs'])

    def test_drift_is_rejected(self):
        with self.assertRaises(ValueError):
            integration.insert_function('different upstream interface','pub fn expected()', 'insert')

    def test_invalid_identity_is_rejected_before_project_write(self):
        with tempfile.TemporaryDirectory() as temp:
            for team,bundle in [('bad','com.valid.app'),('ABCDEFGHIJ','not a bundle')]:
                with self.assertRaises(ValueError): integration.project(Path(temp),team,bundle)
