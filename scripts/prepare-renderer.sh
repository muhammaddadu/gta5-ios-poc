#!/usr/bin/env bash
# Prepare the renderer independently while game acquisition is in progress.
set -euo pipefail
ROOT=$(cd "$(dirname "$0")/.." && pwd)
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
# Dawn's pinned CI supplies this toolchain; native upstream's helper omitted the fetch.
TOOLCHAIN_COMMIT=6fa909e133b92343db2d099e0478448c05ffec1a
mkdir -p "$DAWN/build-tools"
if [[ ! -f "$DAWN/build-tools/apple.toolchain.cmake" ]]; then
  curl --fail --location "https://raw.githubusercontent.com/leetal/ios-cmake/$TOOLCHAIN_COMMIT/ios.toolchain.cmake" \
    -o "$DAWN/build-tools/apple.toolchain.cmake.download"
  mv "$DAWN/build-tools/apple.toolchain.cmake.download" "$DAWN/build-tools/apple.toolchain.cmake"
fi
PATCH="$NATIVE/patches/dawn-ios-bc.patch"
if git -C "$DAWN" apply --check "$PATCH"; then git -C "$DAWN" apply "$PATCH";
else git -C "$DAWN" apply --reverse --check "$PATCH"; fi
# Dawn's generated public headers satisfy the Makefile's prebuilt header layout.
mkdir -p "$NATIVE/tools/dawn/headers/dawn-headers"
if [[ ! -e "$NATIVE/tools/dawn/headers/dawn-headers/include" ]]; then
  ln -s "$DAWN/include" "$NATIVE/tools/dawn/headers/dawn-headers/include"
fi
export CMAKE_BUILD_PARALLEL_LEVEL=${JOBS:-4}
# Preserve upstream and generate a local variant that also bounds the final Ninja invocation.
python3 - "$NATIVE/tools/build-dawn-ios.sh" "$NATIVE/tools/build-dawn-ios.local.sh" <<'PYLOCAL'
from pathlib import Path
import sys
text = Path(sys.argv[1]).read_text()
assert text.count('ninja -C out/ios_arm64') == 1
Path(sys.argv[2]).write_text(text.replace('ninja -C out/ios_arm64', 'ninja -j "${CMAKE_BUILD_PARALLEL_LEVEL:-4}" -C out/ios_arm64'))
PYLOCAL
bash "$NATIVE/tools/build-dawn-ios.local.sh"
# Generated webgpu.h resides under the build output on some Dawn revisions.
# Makefile DAWN_INC overrides the prebuilt paths with source + generated includes.
