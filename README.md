# GTA V local browser and iPhone proof of concept

Original local tooling and instructions for evaluating a locally supplied compatible
WebAssembly build in Chrome, then compiling a native iPhone application.
**Git contains no game build or assets. Chrome 3D gameplay has been verified and a
signed development IPA exported and native phone gameplay confirmed.** See [the measured status](docs/STATUS.md)
for the completed phone installation/gameplay evidence and remaining test limits.

Start with **[the numbered step-by-step reproduction guide](docs/STEP_BY_STEP.md)**
for a fresh setup from this repository through Chrome gameplay, signing, IPA export,
phone transfer and native gameplay validation.

The **[Glue 5 app upgrade](docs/GLUE5_UPGRADE.md)** integrates improved mobile controls,
settings, upscaling and frame pacing while retaining the existing app data.

Everything for this workspace lives under this directory. Private inputs,
third-party checkouts and outputs live under ignored `.local/`. Only original
source, documentation and synthetic tests are committed. The source repository is
[github.com/muhammaddadu/gta5-ios-poc](https://github.com/muhammaddadu/gta5-ios-poc).

## Prerequisites

Apple Silicon Mac, Python 3.11+, current Chrome, full Xcode with its iOS platform component, and enough free space.
The browser data is approximately 21 GB according to upstream; native builds need
additional space for dependencies, generated C, object files and archives. Start
with at least 80 GB free as a planning allowance, not a measured build peak.

```sh
cd /path/to/gta5
python3 --version
xcodebuild -version
# If Xcode reports its iOS platform is missing for a generic device archive:
xcodebuild -downloadPlatform iOS -architectureVariant arm64
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

The owner has authorised acquiring the upstream files for this local POC. Keep
all inputs and derivatives private under `.local/`; the Git exclusion applies to
binaries, data, shaders, translated C and IPAs. POC status does not itself establish
a distribution licence. No game archive files or downloader are committed here.
See [sources and provenance](docs/SOURCES.md).

### Reproduce local-only acquisition

The owner explicitly authorised this route for the private POC. These commands
fetch the pinned helper and manifests into the ignored directory; inspect the
helper before running it. Its source hash is recorded in `upstreams.json`.

```sh
mkdir -p .local
PIN=1474b28dc56d25a3f4bebe11b8fc481a14bf736d
for file in download_game.py download-manifest.json file-inventory.json; do
  curl --fail --location "https://raw.githubusercontent.com/alihammoud21/playgta5/$PIN/$file" -o ".local/$file"
done
python3 scripts/acquire-local.py
# If .local/game does not already exist, link to the acquired mirror.
ln -s mirror/playgta5.com .local/game
python3 scripts/verify_inventory.py
python3 scripts/verify_assets.py
```

Four transfers run concurrently. Every archive and extracted game file is checked
against upstream's manifest. The Windows runtime is skipped. Expect about 42 GB
for retained verified archives plus extracted files; native dependencies/builds
need more. Interrupted acquisition resumes partial transfers; existing differing
files are rejected. Restarting the script requires a conservative free-space
allowance for all archives/files again. Do not run two acquisition processes at
the same time against the same cache. Published hashes establish matching bytes,
not publisher trust, safety or gameplay.

After obtaining a compatible build, copy it into:

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
Run `python3 scripts/verify_inventory.py` for full size/hash validation against the
locally downloaded upstream inventory before claiming installation integrity. Do not treat
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

# Requires the compatible local input set; fails before expensive work if absent.
JOBS=4 bash scripts/build-engine.sh
```

The latter prepares pinned Dawn with upstream's iOS BC-texture patch, builds Metal
support, translates WASM into C and compiles ARM64 `libgta.a`. All derivatives stay
under `.local/upstream/gtav-native/`. The native build can take considerable time
and memory; reduce `JOBS` if this Mac becomes memory constrained. The Dawn renderer and complete iPhone engine library have now compiled on this
Mac. See `docs/BUILD_FIXES.md` for the missing Apple CMake toolchain step that was
resolved during the real build. Runtime compatibility still requires gameplay.

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

### Install on the connected iPhone

The intended phone was described as an iPhone 16 Pro; device inspection identifies
the connected phone as an **iPhone 15 Pro on iOS 27.2**. Record your actual device
rather than relying on a remembered model. Developer Mode was already enabled.

```sh
xcrun devicectl list devices
DEVICE_ID="YOUR_DEVICE_IDENTIFIER" bash scripts/install-ios.sh
```

The helper verifies the local engine and app signature, installs the signed app,
copies shaders to **Documents/shaders** and game data to **Documents/data**, then
terminates an existing instance and launches the app again. The transfer is about
21 GB and can take many minutes over USB. Keep the phone connected. Opening the
app before the transfer finishes can show “Game data not found”; a relaunch after
completion makes it check the folders again. This is not the Glue5 folder layout.

The copied game data remains on the phone and under `.local/game` on the Mac.
Confirm the file inventory and actual 3D world, input and audio. A successful copy
or launch response alone does not prove gameplay.

For manual installation, use Xcode → Window → Devices and Simulators → your device
→ Installed Apps → `+` with the exported development IPA, or open the generated
project and select the connected phone. Use the same unique bundle identifier and
verified Apple account/team as the export. Finder → iPhone → Files → GTA can copy
the two game folders into Documents if you are not using the helper.

The export wrapper generates a private `project.poc.yml` with your bundle ID, so
opening the generated Xcode project does not fall back to upstream's already-taken
`dev.kalki.gta`. Use a fresh suffix if Apple says your chosen identifier is not
available. The concrete account, bundle ID and provisioning details are private
in `.local/`, never in Git.

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
