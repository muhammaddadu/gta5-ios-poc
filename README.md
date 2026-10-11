# GTA V local browser and iPhone proof of concept

Original local tooling and instructions for evaluating a user-supplied compatible
WebAssembly build in Chrome, then compiling a native iPhone application.
**This repository contains no game build or assets. Neither gameplay nor an IPA is
complete.** See [the measured status](docs/STATUS.md).

Everything for this workspace lives under this directory. Private inputs,
third-party checkouts and outputs live under ignored `.local/`. Only original
source, documentation and synthetic tests are committed. No remote is configured.

## Prerequisites

Apple Silicon Mac, Python 3.11+, current Chrome, full Xcode and enough free space.
The browser data is approximately 21 GB according to upstream; native builds need
additional space for dependencies, generated C, object files and archives. Start
with at least 80 GB free as a planning allowance, not a measured build peak.

```sh
cd /path/to/gta5
python3 --version
xcodebuild -version
brew install cmake ninja xcodegen
bash scripts/install-hooks.sh
```

## Required input and permission

These projects require **build `8b0b5899ed` of the unofficial browser port**, not
ordinary retail PC or console files. There is no documented retail-to-WASM
conversion workflow in the reviewed projects. A torrent of a retail installation
would not satisfy the requirement. The browser project's README documents its
own download mechanism, but explicitly claims no redistribution licence for the
game assets. We have not established an authorised source for that build.

Supply files only when you have permission for the particular game code, prepared
data and shaders. Record their source and the basis for permission privately in
`.local/permissions.md`. Local storage, an upstream checksum, an MIT host licence
and owning a retail copy do not establish rights to an unofficial compiled port.
This project does not automate archive retrieval or link to game archive files.
See [sources and provenance](docs/SOURCES.md).

After obtaining a compatible authorised build, copy it into:

```text
.local/game/
  index.html
  b/8b0b5899ed/
    game.wasm
    game.js
    [matching loader and worker files]
    shaders/
      index.json
      [complete matching shader set]
  data/
    [complete prepared game data and metadata]
```

This is a minimum layout, not an exhaustive inventory. Copy the **complete**
browser directory. Do not mix engine, JavaScript, shaders or data from different
builds. Do not replace the browser loader with one from another snapshot.

## Task 1: Chrome

```sh
python3 scripts/verify_assets.py
python3 scripts/serve.py
```

Open [browser diagnostics](http://localhost:8000/__support/) in Chrome. The page
also runs without assets, reporting the missing-input blocker. A passing browser
check verifies basic capabilities, not renderer/shader compatibility or gameplay.

With assets verified, open:

```text
http://localhost:8000/?low=1&fps=30&res=1280x720
```

The server binds only to `127.0.0.1`; leave its terminal running. Ctrl+C stops it.
Use `--port 8001` if another process owns port 8000. Do not expose this experimental
server to the internet. It supplies COOP/COEP headers, WASM MIME, byte ranges and
`POST /data/batch` (including `gz=1`). It never serves this repository, credentials
or the entire `.local/` directory. Opening `index.html` directly is insufficient.

`verify_assets.py` checks minimum file structure, WASM magic and the supported
engine fingerprint. It **does not verify all 21 GB** or detect every missing asset.
Use an independently trusted, complete manifest from your authorised provider for
full size/hash validation before claiming installation integrity. Do not treat
file existence or a matching engine hash as complete asset verification.

Follow [the gameplay checklist](docs/VALIDATION.md). Capture the first DevTools
console error and failed Network request if loading fails. Store evidence and
save games only locally; avoid screenshots containing personal account details.

## Task 2: native iPhone and IPA

The primary route is the MIT-licensed host/tool code of `kalki-kgp/gtav-native`.
The reviewed app spec targets **iOS 26.0**; the engine and Dawn target iOS 17.0.
Keep that app requirement for this POC. Check the actual version in your iPhone's
Settings; “latest iOS” is not a recorded version. Do not assume older-version
support merely because the engine library compiles.

```sh
# This stage needs no game assets; clones pinned source and builds patched wasm2c.
JOBS=4 bash scripts/prepare-native.sh

# Requires the compatible, authorised input set; fails before expensive work if absent.
JOBS=4 bash scripts/build-engine.sh
```

The latter prepares pinned Dawn with upstream's iOS BC-texture patch, builds Metal
support, translates WASM into C and compiles ARM64 `libgta.a`. All derivatives stay
under `.local/upstream/gtav-native/`. The native build can take considerable time
and memory; reduce `JOBS` if this Mac becomes memory constrained. The Dawn/game
stages have not been executed here because inputs are missing. Integration fixes
may still be required; the wrapper is not evidence that these stages compile.

In Xcode → Settings → Accounts, configure your Apple developer account and iOS
signing. A Mac Developer ID certificate is not an iOS development certificate.
The account/provisioning profile must support the app's increased-memory
entitlement. Xcode is the authority for capability availability and signing errors;
we do not promise free-account entitlement support or a seven-day lifetime.
A device-specific development IPA needs a profile covering the intended device.

```sh
TEAM_ID="YOUR_10_CHAR_TEAM" \
BUNDLE_ID="com.yourdomain.gtapoc" \
bash scripts/export-ipa.sh
```

The script creates an original solid-colour icon, generates the Xcode project,
archives the Release scheme and exports with Xcode's `debugging` method. Signing
may need Xcode login, provisioning approval or certificate access on your Mac.
Do not put passwords, certificates or team configuration into Git.

Expected output **only after a successful export**:

```text
.local/dist/GTA.xcarchive
.local/dist/export/GTA.ipa
```

**The IPA contains copyrighted engine code compiled from `game.wasm`, even though
external data/shaders are absent. Keep the IPA, translated C, objects, libraries
and archive private and ignored. Do not publish them or upload them to GitHub
Actions, Releases or any cloud compiler.** A signed IPA is not proof of gameplay.

### Install on your iPhone 16 Pro

1. Connect the iPhone by USB, unlock and trust the Mac. Enable Developer Mode if
   Xcode requests it. Check `xcrun devicectl list devices` for an available device.
2. Open `.local/upstream/gtav-native/ios/app/GTA.xcodeproj` in Xcode. Select the
   `GTA` scheme and your phone, check the same team/bundle ID, then Run. Alternatively
   install the exported development IPA through Xcode → Window → Devices and
   Simulators → your device → Installed Apps → `+`.
3. Use Finder → iPhone → Files → GTA to copy the complete `data` folder and
   `b/8b0b5899ed/shaders` folder into the app's Documents container as **`data` and
   `shaders`**, respectively. Do not place `b/` in Documents for this runtime.
4. Confirm `Documents/data` and `Documents/shaders` exist using Xcode's container
   view/download if available, then launch and follow the gameplay checklist.

The device transfer is approximately 21 GB. Check available iPhone storage first.
For an advanced direct installation of the signed app inside the archive:

```sh
xcrun devicectl device install app --device YOUR_DEVICE_IDENTIFIER \
  .local/dist/GTA.xcarchive/Products/Applications/GTA.app
```

A development IPA is for your provisioned devices. Export/install failure is a
signing or integration blocker to diagnose, not a reason to fabricate an IPA.

### Alternative: Glue 5

[Glue 5](https://github.com/mempage4k/glue5) is a separate Rust/wgpu runtime. We
inspected revision `0ece6f30`; there was no root licence file at that revision, so
we do not vendor its code or artwork. Its upstream checkout is private under
`.local/upstream/glue5`. Its full toolchain has not been built here.

After reviewing its licensing and supplying authorised inputs, upstream documents:

```sh
cd .local/upstream/glue5
# Install mise from its official instructions first; inspect .mise tasks before trust/run.
GLUE5_GAME_DIR="/absolute/path/to/gta5/.local/game" mise run ios:build
GLUE5_GAME_DIR="/absolute/path/to/gta5/.local/game" GLUE5_TEAM="YOUR_TEAM_ID" mise run ios YOUR_DEVICE
GLUE5_GAME_DIR="/absolute/path/to/gta5/.local/game" mise run ios:game YOUR_DEVICE
```

Glue 5 uses **`Documents/game/data` and `Documents/game/b/<build>/shaders`**. Do not
use that layout for gtav-native. Its `ios:build` output is unsigned; `mise run ios`
builds/signs/installs an app, not an exported IPA. Do not promise an IPA from that
command. Our IPA wrapper targets gtav-native only.

## Local validation and commit safeguards

```sh
python3 -m unittest discover -s tests -v
node --check web/check.js
for script in scripts/*.sh; do bash -n "$script"; done
# Stage only these original files, then inspect the exact index.
git add .gitignore AGENTS.md README.md upstreams.json scripts tests docs web
python3 scripts/audit_git.py
git diff --cached --stat
git commit -m "Add asset-free browser and iPhone POC tooling"
```

The pre-commit hook audits staged bytes with a narrow path/type/size allowlist,
rejects symlinks and recognisable private keys. `.gitignore` covers inputs/builds.
These are guardrails; they cannot establish copyright ownership or detect all
secrets/copyrighted text. Review every staged diff. Never force-add `.local/`.
