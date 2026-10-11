#!/usr/bin/env bash
set -euo pipefail
ROOT=$(cd "$(dirname "$0")/.." && pwd)
: "${TEAM_ID:?Set your Apple development Team ID}"
: "${BUNDLE_ID:?Set a unique reverse-domain bundle identifier}"
[[ "$TEAM_ID" =~ ^[A-Z0-9]{10}$ ]] || { echo 'Invalid TEAM_ID' >&2; exit 1; }
[[ "$BUNDLE_ID" =~ ^[A-Za-z][A-Za-z0-9-]*(\.[A-Za-z0-9-]+)+$ ]] || { echo 'Invalid BUNDLE_ID' >&2; exit 1; }
NATIVE="$ROOT/.local/upstream/gtav-native"
test -s "$NATIVE/build/ios/libgta.a" || { echo 'Run build-engine.sh first' >&2; exit 1; }
OUT="$ROOT/.local/dist"
mkdir -p "$OUT"
cd "$NATIVE/ios/app"
printf 'DEVELOPMENT_TEAM = %s\n' "$TEAM_ID" > Local.xcconfig
# Use an original solid-colour icon, not GTA artwork. AppIcon requires a 1024 PNG.
if [[ ! -f App/Assets.xcassets/AppIcon.appiconset/icon-1024.png ]]; then
  python3 - <<'PY'
import struct, zlib
from pathlib import Path
size = 1024
def chunk(kind, body):
    return struct.pack('>I', len(body)) + kind + body + struct.pack('>I', zlib.crc32(kind + body))
raw = (b'\0' + bytes([37, 77, 124]) * size) * size
png = b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', size, size, 8, 2, 0, 0, 0)) + chunk(b'IDAT', zlib.compress(raw)) + chunk(b'IEND', b'')
Path('App/Assets.xcassets/AppIcon.appiconset/icon-1024.png').write_bytes(png)
PY
fi
# Generate a private spec with the same bundle ID the archive uses, so Xcode Run works too.
python3 - "$BUNDLE_ID" <<'PYPROJECT'
from pathlib import Path
import re, sys
source = Path('project.yml').read_text()
changed, count = re.subn(r'(?m)^(\s*PRODUCT_BUNDLE_IDENTIFIER:)\s*\S+', lambda m: m[1] + ' ' + sys.argv[1], source)
assert count == 1
Path('project.poc.yml').write_text(changed)
PYPROJECT
xcodegen generate --spec project.poc.yml
xcodebuild -project GTA.xcodeproj -scheme GTA -configuration Release \
  -destination 'generic/platform=iOS' -archivePath "$OUT/GTA.xcarchive" \
  -derivedDataPath "$ROOT/.local/xcode-derived" \
  -resultBundlePath "$OUT/archive-$(date -u +%Y%m%dT%H%M%SZ).xcresult" \
  -allowProvisioningUpdates DEVELOPMENT_TEAM="$TEAM_ID" PRODUCT_BUNDLE_IDENTIFIER="$BUNDLE_ID" archive
python3 - "$OUT/ExportOptions.plist" "$TEAM_ID" <<'PY'
import plistlib, sys
with open(sys.argv[1], 'wb') as f:
    plistlib.dump({'method': 'debugging', 'teamID': sys.argv[2], 'signingStyle': 'automatic'}, f)
PY
xcodebuild -exportArchive -archivePath "$OUT/GTA.xcarchive" \
  -exportPath "$OUT/export" -exportOptionsPlist "$OUT/ExportOptions.plist" -allowProvisioningUpdates
test -s "$OUT/export/GTA.ipa"
codesign --verify --deep --strict "$OUT/GTA.xcarchive/Products/Applications/GTA.app"
printf '%s\n' "Exported $OUT/export/GTA.ipa (private; contains compiled game code)."
