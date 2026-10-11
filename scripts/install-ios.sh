#!/usr/bin/env bash
# Install the signed local app and transfer only its game data into its own container.
set -euo pipefail
ROOT=$(cd "$(dirname "$0")/.." && pwd)
: "${DEVICE_ID:?Set the intended device identifier from xcrun devicectl list devices}"
GAME_ROOT=${GAME_ROOT:-"$ROOT/.local/game"}
APP=${APP:-"$ROOT/.local/dist/GTA.xcarchive/Products/Applications/GTA.app"}
python3 "$ROOT/scripts/verify_assets.py" --root "$GAME_ROOT"
codesign --verify --deep --strict "$APP"
BUNDLE_ID=$(python3 - "$APP/Info.plist" <<'PY'
import plistlib,sys
with open(sys.argv[1],'rb') as source: print(plistlib.load(source)['CFBundleIdentifier'])
PY
)
mkdir -p "$ROOT/.local/device"
xcrun devicectl device install app --device "$DEVICE_ID" "$APP" \
  --json-output "$ROOT/.local/device/install.json"
# gtav-native reads Documents/shaders and Documents/data (not Glue5's Documents/game).
xcrun devicectl device copy to --device "$DEVICE_ID" --domain-type appDataContainer \
  --domain-identifier "$BUNDLE_ID" --source "$GAME_ROOT/b/8b0b5899ed/shaders" --destination Documents/shaders
xcrun devicectl device copy to --device "$DEVICE_ID" --domain-type appDataContainer \
  --domain-identifier "$BUNDLE_ID" --source "$GAME_ROOT/data" --destination Documents/data
printf '%s\n' "Installed $BUNDLE_ID and copied game folders. Launching; gameplay still needs verification."
xcrun devicectl device process launch --terminate-existing --device "$DEVICE_ID" "$BUNDLE_ID" \
  --json-output "$ROOT/.local/device/launch.json"
