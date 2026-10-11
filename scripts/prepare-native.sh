#!/usr/bin/env bash
# Prepare the MIT native host and its compiler, without fetching game binaries.
set -euo pipefail
ROOT=$(cd "$(dirname "$0")/.." && pwd)
cd "$ROOT"
JOBS=${JOBS:-4}
[[ "$JOBS" =~ ^[1-9][0-9]*$ ]] || { echo 'JOBS must be a positive integer' >&2; exit 1; }
for tool in git cmake ninja xcodegen python3; do
  command -v "$tool" >/dev/null || { echo "Missing $tool; install cmake ninja xcodegen with Homebrew" >&2; exit 1; }
done
[[ "$(uname -m)" == arm64 ]] || { echo 'Apple Silicon required' >&2; exit 1; }
xcodebuild -version
mkdir -p .local/upstream
# Explicit pinned checkouts; reject drift rather than resetting existing work.
checkout() {
  local key=$1 dest=$2 url sha
  url=$(python3 -c 'import json,sys; print(json.load(open("upstreams.json"))[sys.argv[1]]["url"])' "$key")
  sha=$(python3 -c 'import json,sys; print(json.load(open("upstreams.json"))[sys.argv[1]]["commit"])' "$key")
  if [[ ! -d "$dest/.git" ]]; then
    git init "$dest"
    git -C "$dest" remote add origin "$url"
    git -C "$dest" fetch --depth 1 origin "$sha"
    git -C "$dest" checkout --detach FETCH_HEAD
  fi
  [[ "$(git -C "$dest" rev-parse HEAD)" == "$sha" ]] || { echo "Revision mismatch: $dest" >&2; exit 1; }
}
checkout native .local/upstream/gtav-native
NATIVE="$ROOT/.local/upstream/gtav-native"
checkout wabt "$NATIVE/tools/wabt"
git -C "$NATIVE/tools/wabt" submodule update --init --recursive
PATCH="$NATIVE/patches/wabt-atomic-wait-notify.patch"
if git -C "$NATIVE/tools/wabt" apply --check "$PATCH"; then
  git -C "$NATIVE/tools/wabt" apply "$PATCH"
else
  git -C "$NATIVE/tools/wabt" apply --reverse --check "$PATCH"
fi
cmake -S "$NATIVE/tools/wabt" -B "$NATIVE/tools/wabt/build" -G Ninja -DBUILD_TESTS=OFF -DCMAKE_BUILD_TYPE=Release
cmake --build "$NATIVE/tools/wabt/build" --target wasm2c --parallel "$JOBS"
printf '%s\n' 'Native compiler prepared. Next: supply authorised assets and run build-engine.sh.'
