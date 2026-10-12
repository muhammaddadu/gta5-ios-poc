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

    def test_project_keeps_versions_explicit(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            ios=root/'platform/ios';ios.mkdir(parents=True)
            # Original synthetic XcodeGen spec exercising the real project-generation seam.
            spec='settings:\n  PRODUCT_NAME: Example\n  PRODUCT_BUNDLE_IDENTIFIER: local.example\n  DEVELOPMENT_TEAM: ${TEAM}\n  MARKETING_VERSION: 0.1\n  CURRENT_PROJECT_VERSION: 1\n  ASSETCATALOG_COMPILER_APPICON_NAME: Example\nsources:\n  - path: ../shared/Example.icon\ninfo:\n  properties:\n    CFBundleDisplayName: Example\n'
            (ios/'project.yml').write_text(spec)
            integration.project(root,'ABCDEFGHIJ','com.example.poc')
            result=(ios/'project.poc.yml').read_text()
            self.assertIn('CFBundleShortVersionString: $(MARKETING_VERSION)',result)
            self.assertIn('CFBundleVersion: $(CURRENT_PROJECT_VERSION)',result)
            self.assertIn('CURRENT_PROJECT_VERSION: 3',result)
            self.assertIn('MARKETING_VERSION: 1.1',result)

    def test_all_modes_reach_engine_and_patch_is_idempotent(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);base=root/'crates/glue5/src';(base/'ui').mkdir(parents=True)
            fixtures={
                'settings.rs': '    pub game_dir: Option<PathBuf>,\n            game_dir: None,',
                'ui/pages.rs': '    status: &Status,\n    starting: bool,\n                                ui.add_enabled_ui(status.game_dir.is_some() && !starting, |ui| {',
                'ui.rs': 'start_page(&ctx, status, starting, &mut actions, &mut go)',
                'app.rs': "/// Story mode (the browser page's start choice 1).\nconst START_MODE: u32 = 1;\nstart_mode: START_MODE,",
            }
            for name,text in fixtures.items(): (base/name).write_text(text)
            integration.patch_modes(root)
            first={name:(base/name).read_text() for name in fixtures}
            integration.patch_modes(root)
            self.assertEqual(first,{name:(base/name).read_text() for name in fixtures})
            self.assertIn('start_mode: s.start_mode.clamp(1, 3)',first['app.rs'])
            self.assertIn('(1, "Story"), (2, "Playground · GTA V"), (3, "Playground · Test map")',first['ui/pages.rs'])
            self.assertIn('pub start_mode: u32',first['settings.rs'])
