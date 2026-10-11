#!/usr/bin/env bash
set -euo pipefail
ROOT=$(cd "$(dirname "$0")/.." && pwd)
GAME_ROOT=${GAME_ROOT:-"$ROOT/.local/game"}
GAME_ROOT=$(python3 -c 'from pathlib import Path; import sys; print(Path(sys.argv[1]).resolve())' "$GAME_ROOT")
python3 "$ROOT/scripts/verify_assets.py" --root "$GAME_ROOT"
bash "$ROOT/scripts/prepare-native.sh"
bash "$ROOT/scripts/prepare-renderer.sh"
NATIVE="$ROOT/.local/upstream/gtav-native"
DAWN="$NATIVE/tools/dawn-src"
ENGINE_SHA=$(python3 -c 'import hashlib,sys; print(hashlib.file_digest(open(sys.argv[1],"rb"),"sha256").hexdigest())' "$GAME_ROOT/b/8b0b5899ed/game.wasm")
if [[ ! -f "$NATIVE/gen/.engine-sha256" ]] || [[ "$(cat "$NATIVE/gen/.engine-sha256")" != "$ENGINE_SHA" ]]; then
  bash "$NATIVE/scripts/gen.sh" "$GAME_ROOT/b/8b0b5899ed/game.wasm"
  printf '%s\n' "$ENGINE_SHA" > "$NATIVE/gen/.engine-sha256"
fi
make -C "$NATIVE" PLATFORM=ios -j "${JOBS:-4}" DAWN_INC="-I\"$DAWN/include\" -I\"$DAWN/out/ios_arm64/gen/include\""
test -s "$NATIVE/build/ios/libgta.a"
printf '%s\n' 'Engine library built; signing, packaging and device gameplay still require verification.'
