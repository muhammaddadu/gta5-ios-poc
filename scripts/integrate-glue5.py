#!/usr/bin/env python3
"""Apply original POC compatibility changes to an ignored pinned Glue5 checkout."""
from pathlib import Path
import argparse
import json
import re
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


def project(root, team, bundle):
    if not re.fullmatch(r'[A-Z0-9]{10}', team):
        raise ValueError('Invalid Team ID')
    if not re.fullmatch(r'[A-Za-z][A-Za-z0-9-]*(\.[A-Za-z0-9-]+)+', bundle):
        raise ValueError('Invalid bundle ID')
    source = (root / 'platform/ios/project.yml').read_text()
    for key, value in [('PRODUCT_NAME', 'GTA'), ('PRODUCT_BUNDLE_IDENTIFIER', bundle),
                       ('DEVELOPMENT_TEAM', team), ('CFBundleDisplayName', 'GTA V'),
                       ('CURRENT_PROJECT_VERSION', '2'), ('MARKETING_VERSION', '1.1'), ('ASSETCATALOG_COMPILER_APPICON_NAME', 'AppIcon')]:
        source, count = re.subn(r'(?m)^(\s*'+key+r':)\s*[^\n]+', lambda m: m[1]+' '+value, source)
        if count != 1:
            raise ValueError('Expected one project setting: '+key)
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
    project(args.root, args.team, args.bundle)
    print('Applied app identity, existing game/save layout, and conservative iOS defaults.')
