#!/usr/bin/env python3
"""Apply original POC compatibility changes to an ignored pinned Glue5 checkout."""
from pathlib import Path
import argparse
import json
import re
import runpy
import shutil
import struct
import zlib

PROJECT = Path(__file__).resolve().parents[1]
MARKER = 'GTA_POC_COMPAT'


def insert_function(source, signature, body):
    pattern = re.escape(signature) + r'\s*\{\n'
    replacement = signature + ' {\n' + body
    result, count = re.subn(pattern, lambda _: replacement, source)
    if count != 1:
        raise ValueError('Expected exactly one compatibility seam: ' + signature)
    return result


def patch(root):
    runtime = root / 'crates/glue5-runtime/src/lib.rs'
    text = runtime.read_text()
    if MARKER not in text:
        text = insert_function(text, 'pub fn shader_dir(game: &Path) -> PathBuf', '''        // GTA_POC_COMPAT: reuse the existing app's Documents/shaders without copying assets.
        let legacy = game.join("shaders");
        if legacy.join("index.json").is_file() {
            return legacy;
        }
''')
        runtime.write_text(text)
    text = runtime.read_text().replace('data_dir(game).is_dir()', 'data_dir(game).join("manifest.json").is_file()')
    runtime.write_text(text)
    paths = root / 'crates/glue5/src/paths.rs'
    text = paths.read_text()
    if MARKER not in text:
        text = insert_function(text, 'pub fn user_dir() -> Result<PathBuf>', '''    // GTA_POC_COMPAT: keep existing saves/settings in the same app container.
    #[cfg(target_os = "ios")]
    {
        let docs = sdl3::filesystem::get_user_folder(sdl3::filesystem::Folder::DOCUMENTS)
            .map_err(|e| anyhow::anyhow!("no Documents directory: {e}"))?;
        let legacy = docs.join("userdata");
        std::fs::create_dir_all(&legacy)?;
        return Ok(legacy);
    }
''')
        anchor = r'(dirs\.push\(docs\.join\("game"\)\);)'
        text, count = re.subn(anchor, 'dirs.push(docs.to_path_buf()); // existing Documents/data + shaders\n            '+r'\1', text)
        if count != 1:
            raise ValueError('Expected one iOS game-directory seam')
        text = text.replace('iPhone › Files › Glue 5', 'iPhone › Files › GTA V').replace('On My iPhone › Glue 5', 'On My iPhone › GTA V')
        paths.write_text(text)
    # Repair compatibility checkouts produced before SDL borrowed-path handling was corrected.
    text = paths.read_text().replace("dirs.push(docs.clone()); // existing Documents/data + shaders", "dirs.push(docs.to_path_buf()); // existing Documents/data + shaders")
    paths.write_text(text)
    text = paths.read_text()
    if '#[cfg(not(target_os = "ios"))]' not in text:
        text = re.sub(r'(?m)^(    )(sdl3::filesystem::get_pref_path[^\n]+)$',
                      lambda m: m[1]+'#[cfg(not(target_os = "ios"))]\n'+m[1]+'{\n'+m[1]+'    '+m[2]+'\n'+m[1]+'}', text)
        paths.write_text(text)
    settings = root / 'crates/glue5/src/settings.rs'
    text = settings.read_text()
    if MARKER not in text:
        text, count = re.subn(r'(low_memory:\s*)(MOBILE\s*&&[^,]+),',
                             r'\1cfg!(target_os = "ios") || (\2), // GTA_POC_COMPAT: conservative first launch', text, count=1)
        if count != 1:
            raise ValueError('Expected one low-memory default seam')
        settings.write_text(text)
    # Mobile UX: preserve readable native UI while lowering the initial scene's GPU cost.
    text = settings.read_text().replace('if MOBILE { 720 } else { 1080 }', 'if MOBILE { 640 } else { 1080 }')
    text = text.replace('if MOBILE { 0.6 } else { 0.9 }', 'if MOBILE { 0.55 } else { 0.9 }')
    settings.write_text(text)
    pages = root / 'crates/glue5/src/ui/pages.rs'
    if pages.is_file():
        text = pages.read_text().replace('"GLUE 5"', '"GTA V"')
        text = text.replace('let text = dir.display().to_string();',
                            'let text = if MOBILE { "Stored on this device".to_owned() } else { dir.display().to_string() };')
        pages.write_text(text)
    touch = root / 'crates/glue5/src/touch.rs'
    if touch.is_file():
        text = touch.read_text()
        if '.max(22.0)' not in text:
            text = text.replace('b.radius * self.scale * 1.25', '(b.radius * self.scale * 1.25).max(22.0)')
        touch.write_text(text)
    # Preserve backend package names/attribution. Only the error-dialog product label changes.
    app_lib = root / 'crates/glue5/src/lib.rs'
    text = app_lib.read_text().replace('"Glue 5"', '"GTA V"')
    app_lib.write_text(text)



def patch_modes(root):
    """Restore the engine's three launch choices omitted by the pinned host."""
    def replace(path, old, new):
        text = path.read_text()
        if path.name == 'pages.rs' and 'GTA_POC_HOME' in text:
            return
        if new in text:
            return
        if text.count(old) != 1:
            raise ValueError('Expected one launch-mode seam: ' + str(path))
        path.write_text(text.replace(old, new))
    base = root / 'crates/glue5/src'
    replace(base/'settings.rs', '    pub game_dir: Option<PathBuf>,',
            '    pub game_dir: Option<PathBuf>,\n    /// GTA_POC_MODES: engine launch choice, persisted with app settings.\n    pub start_mode: u32,')
    replace(base/'settings.rs', '            game_dir: None,',
            '            game_dir: None,\n            start_mode: 1,')
    replace(base/'ui/pages.rs', '    status: &Status,\n    starting: bool,',
            '    status: &Status,\n    settings: &mut Settings,\n    starting: bool,')
    replace(base/'ui/pages.rs', '                                ui.add_enabled_ui(status.game_dir.is_some() && !starting, |ui| {',
            '                                ui.add_enabled_ui(status.game_dir.is_some() && !starting, |ui| {\n'
            '                                    ui.label("Game mode");\n'
            '                                    for (mode, label) in [(1, "Story"), (2, "Playground · GTA V"), (3, "Playground · Test map")] {\n'
            '                                        if ui.add_sized([menu_width, 44.0 * scale], egui::Button::new(label).selected(settings.start_mode == mode)).clicked() {\n'
            '                                            settings.start_mode = mode;\n'
            '                                        }\n'
            '                                    }\n'
            '                                    ui.label(RichText::new("Choose a mode, then Play. Reopen the app to switch modes.").small().color(theme::MUTED));')
    replace(base/'ui.rs', 'start_page(&ctx, status, starting, &mut actions, &mut go)',
            'start_page(&ctx, status, settings, starting, &mut actions, &mut go)')
    replace(base/'app.rs', 'start_mode: START_MODE,',
            'start_mode: s.start_mode.clamp(1, 3),')
    replace(base/'app.rs', '/// Story mode (the browser page\'s start choice 1).\nconst START_MODE: u32 = 1;\n',
            '// GTA_POC_MODES: the home selection supplies the engine launch mode.\n')



def patch_resizing(root):
    """Let mobile render targets follow fold/unfold window changes safely."""
    path = root / 'crates/glue5/src/app.rs'
    text = path.read_text()
    marker = 'GTA_POC_RESIZE'
    if marker in text:
        return
    old = 'if MOBILE || w == 0 || h == 0 {'
    if text.count(old) != 1:
        raise ValueError('Expected one mobile resize guard')
    text = text.replace(old, 'if w == 0 || h == 0 {')
    old = 'let size = settings::render_size((w, h), self.settings.render_scale(), game.started.low_memory);'
    if text.count(old) != 1:
        raise ValueError('Expected one render resize calculation')
    text = text.replace(old, '// GTA_POC_RESIZE: mobile windows can resize when the device folds.\n'
        '        // Preserve mobile next-launch graphics settings while following the live window.\n'
        '        let scale = if MOBILE { game.started.render_scale } else { self.settings.render_scale() };\n'
        '        let size = settings::render_size((w, h), scale, game.started.low_memory);')
    old = '            input.resize(size.0, size.1);'
    if text.count(old) != 1:
        raise ValueError('Expected one engine resize submission')
    text = text.replace(old, '            input.release_all();\n'
        '            self.touch.clear();\n'
        '            glue5_runtime::input::set_gamepad(0, Gamepad::default());\n'+old)
    text = text.replace('Phone windows never change size; their back\n    /// buffer is the one they started with.',
                        'Mobile windows also resize across display transitions.')
    path.write_text(text)


def project(root, team, bundle):
    if not re.fullmatch(r'[A-Z0-9]{10}', team):
        raise ValueError('Invalid Team ID')
    if not re.fullmatch(r'[A-Za-z][A-Za-z0-9-]*(\.[A-Za-z0-9-]+)+', bundle):
        raise ValueError('Invalid bundle ID')
    source = (root / 'platform/ios/project.yml').read_text()
    for key, value in [('PRODUCT_NAME', 'GTA'), ('PRODUCT_BUNDLE_IDENTIFIER', bundle),
                       ('DEVELOPMENT_TEAM', team), ('CFBundleDisplayName', 'GTA V'),
                       ('CURRENT_PROJECT_VERSION', '4'), ('MARKETING_VERSION', '1.1'), ('ASSETCATALOG_COMPILER_APPICON_NAME', 'AppIcon')]:
        source, count = re.subn(r'(?m)^(\s*'+key+r':)\s*[^\n]+', lambda m: m[1]+' '+value, source)
        if count != 1:
            raise ValueError('Expected one project setting: '+key)
    source, count = re.subn(r'(?m)^(\s*)CFBundleDisplayName: GTA V$',
        lambda m: m[0]+'\n'+m[1]+'CFBundleShortVersionString: $(MARKETING_VERSION)\n'+m[1]+'CFBundleVersion: $(CURRENT_PROJECT_VERSION)', source)
    if count != 1:
        raise ValueError('Expected one Info.plist version seam')
    source, count = re.subn(r'(?m)^(\s*- path:)\s*\.\./shared/[^\n]+',
                           lambda m: m[1]+' Assets.xcassets', source)
    if count != 1:
        raise ValueError('Expected one icon resource entry')
    dest = root / 'platform/ios/Assets.xcassets/AppIcon.appiconset'
    dest.mkdir(parents=True, exist_ok=True)
    old = PROJECT / '.local/upstream/gtav-native/ios/app/App/Assets.xcassets/AppIcon.appiconset/icon-1024.png'
    if old.is_file():
        shutil.copyfile(old, dest / 'icon-1024.png')
    else:
        # Original solid-colour POC icon, identical to the baseline icon.
        def chunk(kind, body):
            return struct.pack('>I', len(body)) + kind + body + struct.pack('>I', zlib.crc32(kind + body))
        raw = (b'\0' + bytes([37, 77, 124]) * 1024) * 1024
        png = b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB',1024,1024,8,2,0,0,0)) + chunk(b'IDAT',zlib.compress(raw)) + chunk(b'IEND',b'')
        (dest/'icon-1024.png').write_bytes(png)
    (dest/'Contents.json').write_text(json.dumps({'images':[{'filename':'icon-1024.png','idiom':'universal','platform':'ios','size':'1024x1024'}], 'info':{'author':'xcode','version':1}}, indent=2)+'\n')
    (root/'platform/ios/project.poc.yml').write_text(source)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, default=PROJECT/'.local/upstream/glue5-integrated')
    parser.add_argument('--team', required=True)
    parser.add_argument('--bundle', required=True)
    args = parser.parse_args()
    patch(args.root)
    patch_modes(args.root)
    patch_resizing(args.root)
    project(args.root, args.team, args.bundle)
    handheld = runpy.run_path(str(PROJECT/'scripts/duo_ui.py'))
    handheld['patch'](args.root)
    handheld['patch_home'](args.root)
    handheld['patch_input_safety'](args.root)
    handheld['patch_settings_targets'](args.root)
    handheld['patch_settings_scroll_tests'](args.root)
    handheld['add_settings_target_tests'](args.root)
    print('Applied app identity, existing game/save layout, and conservative iOS defaults.')
