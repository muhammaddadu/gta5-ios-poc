#!/usr/bin/env bash
# Original synthetic module: f() returns 42. No game code or data.
set -euo pipefail
ROOT=$(cd "$(dirname "$0")/.." && pwd)
cd "$ROOT"
WABT="$ROOT/.local/upstream/gtav-native/tools/wabt"
test -x "$WABT/build/wasm2c" || { echo 'Run prepare-native.sh first' >&2; exit 1; }
mkdir -p .local/smoke
python3 - <<'PY'
from pathlib import Path
Path('.local/smoke/probe.wasm').write_bytes(bytes.fromhex('0061736d010000000105016000017f03020100070501016600000a06010400412a0b'))
PY
"$WABT/build/wasm2c" -n probe -o .local/smoke/probe.c .local/smoke/probe.wasm
xcrun --sdk iphoneos clang -arch arm64 -miphoneos-version-min=17.0 \
  -DWASM_RT_MEMCHECK_BOUNDS_CHECK=1 -I "$WABT/wasm2c" \
  -c .local/smoke/probe.c -o .local/smoke/probe.o
file .local/smoke/probe.o
printf '%s\n' 'Synthetic translation/ARM64 compile passed. This does not validate the game or native host.'
