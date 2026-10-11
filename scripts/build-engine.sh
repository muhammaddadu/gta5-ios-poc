#!/usr/bin/env bash
set -euo pipefail
ROOT=$(cd "$(dirname "$0")/.." && pwd)
GAME_ROOT=${GAME_ROOT:-"$ROOT/.local/game"}
GAME_ROOT=$(python3 -c 'from pathlib import Path; import sys; print(Path(sys.argv[1]).resolve())' "$GAME_ROOT")
python3 "$ROOT/scripts/verify_assets.py" --root "$GAME_ROOT"
bash "$ROOT/scripts/prepare-native.sh"
cd "$ROOT"
NATIVE="$ROOT/.local/upstream/gtav-native"
DAWN="$NATIVE/tools/dawn-src"
SHA=$(python3 -c 'import json; print(json.load(open("upstreams.json"))["dawn"]["commit"])')
if [[ ! -d "$DAWN/.git" ]]; then
  git init "$DAWN"
  git -C "$DAWN" remote add origin https://dawn.googlesource.com/dawn
  git -C "$DAWN" fetch --depth 1 origin "$SHA"
  git -C "$DAWN" checkout --detach FETCH_HEAD
fi
[[ "$(git -C "$DAWN" rev-parse HEAD)" == "$SHA" ]] || { echo 'Dawn revision mismatch' >&2; exit 1; }
PATCH="$NATIVE/patches/dawn-ios-bc.patch"
if git -C "$DAWN" apply --check "$PATCH"; then git -C "$DAWN" apply "$PATCH";
else git -C "$DAWN" apply --reverse --check "$PATCH"; fi
# Dawn's generated public headers satisfy the Makefile's prebuilt header layout.
mkdir -p "$NATIVE/tools/dawn/headers/dawn-headers"
if [[ ! -e "$NATIVE/tools/dawn/headers/dawn-headers/include" ]]; then
  ln -s "$DAWN/include" "$NATIVE/tools/dawn/headers/dawn-headers/include"
fi
export CMAKE_BUILD_PARALLEL_LEVEL=${JOBS:-4}
bash "$NATIVE/tools/build-dawn-ios.sh"
# Generated webgpu.h resides under the build output on some Dawn revisions.
# Makefile DAWN_INC overrides the prebuilt paths with source + generated includes.
ENGINE_SHA=$(python3 -c 'import hashlib,sys; print(hashlib.file_digest(open(sys.argv[1],"rb"),"sha256").hexdigest())' "$GAME_ROOT/b/8b0b5899ed/game.wasm")
if [[ ! -f "$NATIVE/gen/.engine-sha256" ]] || [[ "$(cat "$NATIVE/gen/.engine-sha256")" != "$ENGINE_SHA" ]]; then
  bash "$NATIVE/scripts/gen.sh" "$GAME_ROOT/b/8b0b5899ed/game.wasm"
  printf '%s\n' "$ENGINE_SHA" > "$NATIVE/gen/.engine-sha256"
fi
make -C "$NATIVE" PLATFORM=ios -j "${JOBS:-4}" DAWN_INC="-I\"$DAWN/include\" -I\"$DAWN/out/ios_arm64/gen/include\""
test -s "$NATIVE/build/ios/libgta.a"
printf '%s\n' 'Engine library built; signing, packaging and device gameplay still require verification.'
