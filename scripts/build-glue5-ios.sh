#!/usr/bin/env bash
# Build an update to the existing app using pinned Glue5, preserving the original IPA.
set -euo pipefail
ROOT=$(cd "$(dirname "$0")/.." && pwd)
cd "$ROOT"
: "${TEAM_ID:?Set the verified Apple development Team ID}"
: "${BUNDLE_ID:?Use the installed app bundle ID to preserve its container}"
command -v mise >/dev/null || { echo 'Install mise with Homebrew first' >&2; exit 1; }
JOBS=${JOBS:-4}
[[ "$JOBS" =~ ^[1-9][0-9]*$ ]] || { echo 'Invalid JOBS' >&2; exit 1; }
python3 scripts/verify_assets.py
PIN=$(python3 -c 'import json; print(json.load(open("upstreams.json"))["glue5_integration"]["commit"])')
RUST=$(python3 -c 'import json; print(json.load(open("upstreams.json"))["glue5_integration"]["rust"])')
SOURCE="$ROOT/.local/upstream/glue5-integrated"
if [[ ! -d "$SOURCE/.git" ]]; then
  git init "$SOURCE"
  git -C "$SOURCE" remote add origin https://github.com/mempage4k/glue5.git
  git -C "$SOURCE" fetch --depth 1 origin "$PIN"
  git -C "$SOURCE" checkout --detach FETCH_HEAD
fi
[[ "$(git -C "$SOURCE" rev-parse HEAD)" == "$PIN" ]] || { echo 'Glue5 revision mismatch' >&2; exit 1; }
python3 scripts/integrate-glue5.py --root "$SOURCE" --team "$TEAM_ID" --bundle "$BUNDLE_ID"
cd "$SOURCE"
mise trust .mise/config.toml
mise install "rust@$RUST"
mise exec "rust@$RUST" -- rustup target add aarch64-apple-ios
mise exec "rust@$RUST" -- bash .mise/tasks/setup
export GLUE5_GAME_DIR="$ROOT/.local/game"
export CARGO_BUILD_JOBS="$JOBS" CMAKE_BUILD_PARALLEL_LEVEL="$JOBS"
export IPHONEOS_DEPLOYMENT_TARGET=16.4
mise exec "rust@$RUST" -- cargo rustc --locked --release -p glue5 --lib \
  --crate-type staticlib --target aarch64-apple-ios
xcodegen generate --spec platform/ios/project.poc.yml
OUT="$ROOT/.local/dist/glue5"
mkdir -p "$OUT"
xcodebuild -project platform/ios/Glue5.xcodeproj -scheme Glue5 -configuration Release \
  -destination 'generic/platform=iOS' -archivePath "$OUT/GTA.xcarchive" \
  -derivedDataPath "$ROOT/.local/glue5-xcode-derived" -allowProvisioningUpdates archive
python3 - "$OUT/ExportOptions.plist" "$TEAM_ID" <<'PY'
import plistlib,sys
with open(sys.argv[1],'wb') as f:
    plistlib.dump({'method':'debugging','teamID':sys.argv[2],'signingStyle':'automatic'},f)
PY
xcodebuild -exportArchive -archivePath "$OUT/GTA.xcarchive" -exportPath "$OUT/export" \
  -exportOptionsPlist "$OUT/ExportOptions.plist" -allowProvisioningUpdates
codesign --verify --deep --strict "$OUT/GTA.xcarchive/Products/Applications/GTA.app"
test -s "$OUT/export/GTA.ipa"
printf '%s\n' "Updated IPA: $OUT/export/GTA.ipa. Original IPA is unchanged."
