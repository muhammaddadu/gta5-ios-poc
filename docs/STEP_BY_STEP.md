# Reproduce the web and iPhone POC

Follow this guide on an Apple Silicon Mac, from a copy of this repository. It
covers the local Chrome game and the native iPhone app/IPA that we actually used.
The browser uses WebAssembly/WebGPU; the phone uses compiled ARM64 code and Metal.
The phone does not stream the game from the Mac, and does not need the web server.

[Verified results](STATUS.md) · [Build fixes](BUILD_FIXES.md) · [Test checklist](VALIDATION.md)

## 1. Open this repository in Terminal

Get a copy of this repository's committed source. The validated checkout has no
Git remote configured, so there is no public clone URL supplied by this guide.
A source-only copy does not include the game, dependencies, IPA or credentials.

```sh
cd /path/to/gta5
export POC_ROOT="$PWD"
git status --short --branch
mkdir -p .local
bash scripts/install-hooks.sh
```

Keep every command in this guide in that Terminal session. If you open another
Terminal, return to the repository and set `POC_ROOT` again. `.local/` is ignored
by Git and holds all downloaded and generated material. Preserve existing files
and unrelated Git changes; do not force-add `.local/`.

## 2. Install and check the Mac prerequisites

Use an Apple Silicon Mac, current Google Chrome, Python 3.11+ and full Xcode.
This POC used Python 3.12 and Xcode 26.4.1. The native app currently targets iOS
26.0 or newer. The connected phone we tested was an iPhone 15 Pro on iOS 27.2.
Other hardware/software combinations need their own gameplay verification.

Allow about 100 GB free on the Mac as a conservative planning allowance for
retained archives, extracted files, native builds and Xcode components. This is
not a measured peak requirement. Allow at least 25 GB free on the phone for the
app, data and saves. Acquiring files requires internet; later game execution is
local. Homebrew and Xcode components install into their normal system locations;
all game/project inputs and outputs stay inside `.local/`.

Install Homebrew from its official instructions if `brew` is unavailable. Then:

```sh
uname -m
python3 --version
git --version
xcodebuild -version
xcode-select -p
brew install cmake ninja xcodegen
```

Expected architecture: `arm64`. Xcode's developer directory should point at full
Xcode, not just Command Line Tools. If necessary, select your installed Xcode:

```sh
sudo xcode-select --switch /Applications/Xcode.app/Contents/Developer
```

Complete Xcode's normal first-launch setup yourself if it requests it. For web
only, no Apple account or iOS platform component is needed. For the phone build,
if Xcode reports that its iOS platform is not installed:

```sh
xcodebuild -downloadPlatform iOS -architectureVariant arm64
```

We needed the matching iOS 26.4.1 runtime even though `xcodebuild -showsdks`
already listed an iPhoneOS compiler SDK. Installing it fixed both the generic
archive destination and asset-catalogue compilation. Use the component matching
your installed Xcode; do not assume an arbitrary simulator version will suffice.

## 3. Acquire the exact compatible browser build locally

The required build is `8b0b5899ed`, with the complete matching JavaScript,
`game.wasm`, shaders and prepared data. Ordinary PC/console installation files
alone are not compatible. No retail-to-WASM conversion is provided here.

The owner authorised upstream release acquisition for this local POC. The source
repository includes acquisition tooling, not the game files. Keep downloads and
all derivatives private and out of Git; POC use does not grant redistribution
rights. The provenance and upstream references are in [SOURCES.md](SOURCES.md).

Download the pinned upstream helper and inventories:

```sh
cd "$POC_ROOT"
PIN=$(python3 -c 'import json; print(json.load(open("upstreams.json"))["browser_reference"]["commit"])')
for file in download_game.py download-manifest.json file-inventory.json; do
  curl --fail --location \
    "https://raw.githubusercontent.com/alihammoud21/playgta5/$PIN/$file" \
    -o ".local/$file"
done
```

Inspect `.local/download_game.py` before running it. Our wrapper checks the helper
and both inventories against the SHA-256 fingerprints in `upstreams.json`.

```sh
set -o pipefail
python3 scripts/acquire-local.py 2>&1 | tee .local/acquire.log
```

Wait for `Complete`. There are 14 archives, approximately 21.2 GB downloaded.
Four transfers run concurrently. Archive hashes and extracted-file hashes are
checked; the Windows runtime is not extracted. Archives are retained, so archives
plus extracted files occupy roughly 42 GB. Interrupted transfers resume when you
rerun this command; differing existing files are rejected rather than overwritten.
Run only one acquisition process against the cache at a time. If upstream files
become unavailable or hashes change, stop and investigate; do not disable checks.

## 4. Link the game directory and verify the entire inventory

```sh
cd "$POC_ROOT"
if [ ! -e .local/game ] && [ ! -L .local/game ]; then
  ln -s mirror/playgta5.com .local/game
fi
python3 scripts/verify_inventory.py | tee .local/verify-inventory.log
python3 scripts/verify_assets.py | tee .local/verify-assets.log
```

The complete local inventory should report **12,482 files** and
**21,158,604,965 bytes**. The engine fingerprint should be:

```text
11ca8d2c04c5e843d18ff4aea4899d72c86973c6b031df334e67c446b2ae83e0
```

`verify_assets.py` alone checks minimum structure and the engine hash; it is not
full asset verification. `verify_inventory.py` hashes every game file against the
pinned inventory. Matching published bytes does not independently prove safety.

The relevant paths are:

```text
.local/game/index.html
.local/game/b/8b0b5899ed/game.wasm
.local/game/b/8b0b5899ed/game.js
.local/game/b/8b0b5899ed/shaders/index.json
.local/game/data/manifest.json
```

The mirror contains additional loader, worker, shader and data files. Keep the
complete set together. An existing `.local/game` is preserved by the linking
command; inspect its target if verification finds the wrong build or missing files.

## 5. Start the browser server and check Chrome

```sh
cd "$POC_ROOT"
python3 scripts/serve.py
```

Keep this Terminal running. Open
[http://localhost:8000/__support/](http://localhost:8000/__support/) in Chrome.
Expect secure context, cross-origin isolation, shared memory, Memory64 and WebGPU
adapter/device checks to pass, plus the real engine range check.

Enable Chrome's graphics acceleration setting if WebGPU is unavailable. Check
`chrome://gpu` for driver/capability errors. A successful support page is not yet
gameplay. The server provides WASM MIME, byte ranges and the engine's batch reads;
double-clicking `index.html` does not provide that transport.

If port 8000 is already occupied, choose another port:

```sh
python3 scripts/serve.py --port 8001
```

Use that port in every URL. The server binds only to this Mac's loopback address.

## 6. Play GTA V locally in Chrome

Open:

```text
http://localhost:8000/?low=1&fps=30&res=1280x720
```

1. Choose **Sandbox Mode**.
2. Choose **GTA V Map**. This was our verified browser route.
3. Wait for a textured 3D world and the player to appear.
4. Click the canvas to capture input and enable audio, then use WASD to move.
5. Use `=` to display FPS. Esc releases mouse capture; Shift+P changes keyboard mode.

We directly observed world rendering and keyboard walking, with an overlay sample
around 31 FPS at the 30 FPS cap. Story Mode is another menu option, but it was not
comprehensively validated in this POC. A loading percentage or HUD alone is not a
successful result. For a failure, capture the first DevTools console error and
failed Network request before making changes.

Stop the web server with **Ctrl+C in its Terminal** after testing. The phone build
and app do not require that server. We stopped it after the owner accepted browser
validation. Assets and browser saves remain local.

## 7. Prepare the native compiler and build the phone engine

Use a second Terminal, or stop the browser server first. If this is a new
Terminal, set its repository path explicitly:

```sh
cd /path/to/gta5
export POC_ROOT="$PWD"
set -o pipefail
JOBS=4 bash scripts/prepare-native.sh 2>&1 | tee .local/prepare-native.log
JOBS=4 bash scripts/build-engine.sh 2>&1 | tee .local/build-engine.log
```

The scripts clone pinned native host, wabt and Dawn source under `.local/upstream`,
build patched `wasm2c`, translate the engine into 256 C files, compile those files
to iPhone ARM64 and build Dawn's Metal renderer. Generated engine code is about
1 GB before compilation. Keep it, objects and libraries out of Git.

`prepare-renderer.sh` supplies the Apple CMake toolchain step omitted by upstream's
native helper and includes source/generated Dawn headers. The fix is already in
this repo; you do not need to patch the upstream script manually. `JOBS=4` bounds
build concurrency; use `JOBS=2` if necessary. Do not run two builds against the same
output directory simultaneously.

Successful outputs include:

```text
.local/upstream/gtav-native/build/ios/libgta.a
.local/upstream/gtav-native/tools/dawn-src/out/ios_arm64/src/dawn/native/libwebgpu_dawn.a
```

Our session overlapped acquisition, translation and renderer work to save time.
This guide deliberately orders those steps so a fresh reproduction has clear
checkpoints. An incremental repeat should reuse matching generated/build outputs.

## 8. Connect the phone and authenticate the correct Apple account

1. Connect the intended phone by USB, unlock it and trust the Mac.
2. Enable Developer Mode on the phone if required; complete its restart/confirmation.
3. Open **Xcode → Settings → Apple Accounts** and sign in to your Apple account.
4. Complete password and two-factor verification yourself. Never put passwords in
   Terminal commands, this repository or a chat.
5. Inspect the account's team and choose the team you intend to use for signing.
   A Mac Developer ID certificate alone does not establish the intended iOS account.

```sh
xcrun devicectl list devices
```

Confirm the intended iPhone is available/paired. Record its identifier for Step 10.
The actual tested phone identified as an iPhone 15 Pro, despite the initial model
being described as a 16 Pro. Use the device information Xcode reports.

The signing profile must cover the phone and the increased-memory entitlement.
Xcode will report if the selected account/team cannot provision it. Do not assume
all Personal Teams have the same limits or expiry: our actual generated profile
included the entitlement and had a one-year recorded expiry.

## 9. Archive, sign and export the IPA

Set your verified team ID and a unique bundle identifier. A fresh suffix avoids
collisions with app identifiers already registered by someone else:

```sh
cd "$POC_ROOT"
export TEAM_ID="YOUR_10_CHAR_TEAM_ID"
SUFFIX=$(python3 -c 'import uuid; print(uuid.uuid4().hex[:12])')
export BUNDLE_ID="com.yourdomain.gtapoc.poc$SUFFIX"
set -o pipefail
bash scripts/export-ipa.sh 2>&1 | tee .local/export-ipa.log
```

Replace `com.yourdomain` and the team placeholder. Keep the chosen bundle ID for
subsequent rebuilds/installations; do not generate a new ID for every update.
Changing the ID creates a separate app/container requiring another data copy.

The script creates an original solid-colour icon and a private XcodeGen spec with
your bundle ID, archives the GTA scheme and exports a development IPA. We initially
hit an unavailable bundle ID; a new unique suffix resolved it. If macOS asks to
let `codesign` use the development key, enter your Mac login-keychain password in
the system prompt and approve the signing request yourself. Do not share or store
that password. Signing can pause until you complete that prompt.

Wait for both `ARCHIVE SUCCEEDED` and `EXPORT SUCCEEDED`. Outputs:

```text
.local/dist/GTA.xcarchive/Products/Applications/GTA.app
.local/dist/export/GTA.ipa
```

```sh
codesign --verify --deep --strict \
  .local/dist/GTA.xcarchive/Products/Applications/GTA.app
ls -lh .local/dist/export/GTA.ipa
```

Our exported IPA was **66,405,871 bytes** and passed signature checks. Size can
change with build/signing settings. It includes compiled game code, but not the
external data/shaders. Keep the IPA, archive, provisioning profiles, logs and
signing configuration private under `.local/`. Do not commit or distribute them.

## 10. Install, transfer all files and relaunch

Use the identifier of your own connected phone from Step 8:

```sh
cd "$POC_ROOT"
export DEVICE_ID="YOUR_DEVICE_IDENTIFIER"
set -o pipefail
bash scripts/install-ios.sh 2>&1 | tee .local/install-ios.log
```

The helper installs the signed archived app corresponding to the exported IPA,
copies both folders and launches it. It reads the bundle ID from that app's plist,
so it does not assume upstream's default identifier.

| Mac source | Phone app-container destination |
| --- | --- |
| `.local/game/data` | `Documents/data` |
| `.local/game/b/8b0b5899ed/shaders` | `Documents/shaders` |

The data transfer is about **20.95 GB**, plus shaders, and can take many minutes.
Keep the cable connected until the entire command finishes. Do not treat the
initial “App installed” response as completed transfer.

If you open the app early, **Game data not found** can appear because the manifest
has not arrived. We encountered exactly that. The helper now uses
`--terminate-existing` after both copies, so the app restarts and checks again.
This preserves the app's data. You can explicitly relaunch after a completed copy:

```sh
xcrun devicectl device process launch --terminate-existing \
  --device "$DEVICE_ID" "$BUNDLE_ID"
```

The correct path is `Documents/data/manifest.json`, not
`Documents/data/data/manifest.json`, and not Glue5's `Documents/game/data`.
If it still fails after a complete transfer, inspect the app's container in Xcode
or with the inventory commands below. Do not delete the game data as a first step.

To install the exported IPA manually, use **Xcode → Window → Devices and Simulators
→ your phone → Installed Apps → +**. The data/shader transfer is still required.
Finder's device Files view can transfer the two folders into this app's Documents.

## 11. Verify phone files, then test actual gameplay

With the phone still connected and the same `DEVICE_ID`/`BUNDLE_ID` set:

```sh
cd "$POC_ROOT"
mkdir -p .local/device
xcrun devicectl device info files --device "$DEVICE_ID" \
  --domain-type appDataContainer --domain-identifier "$BUNDLE_ID" \
  --subdirectory Documents/data --recurse \
  --json-output .local/device/data-final.json > .local/device/data-final.log
python3 scripts/verify-device-files.py --root .local/game/data \
  --inventory .local/device/data-final.json

xcrun devicectl device info files --device "$DEVICE_ID" \
  --domain-type appDataContainer --domain-identifier "$BUNDLE_ID" \
  --subdirectory Documents/shaders --recurse \
  --json-output .local/device/shaders-final.json > .local/device/shaders-final.log
python3 scripts/verify-device-files.py --root .local/game/b/8b0b5899ed/shaders \
  --inventory .local/device/shaders-final.json
```

Our device matched **5,817 data files / 20,945,061,654 bytes** and
**6,615 shader files / 144,792,037 bytes**, with no additional files. This compares
remote paths and sizes; it does not read back all phone hashes. Full local SHA-256
verification happened before the transfer.

Open GTA V on the phone. Check a rendered 3D world, movement using the touch
controls and sound. Allow initial shader compilation/loading to settle. The owner
confirmed all three worked. One early native log sample reported 59.5 FPS with
zero added GPU validation errors, but there were initial skipped shader draws and
a 653 ms hitch. This was a functional POC, not a sustained performance benchmark.

For diagnostics, pull only this app's log into the ignored directory:

```sh
xcrun devicectl device copy from --device "$DEVICE_ID" \
  --domain-type appDataContainer --domain-identifier "$BUNDLE_ID" \
  --source Documents/game.log --destination .local/device/game.log
```

A launch response, frame counter or successful build alone is not gameplay proof.
Use [VALIDATION.md](VALIDATION.md) for longer-session, save/reload, thermal and
mission testing. Disconnect the phone after file transfer and desired validation
finish. The installed native app runs from its own files without the Mac server.

## 12. Re-run later and keep Git clean

**Browser:** from this repo, run `python3 scripts/serve.py`, open the Step 6 URL,
then stop with Ctrl+C when done. The server was stopped at the end of our session.

**Phone:** reopen the installed GTA V app. If its provisioning expires, rebuild
and reinstall with the same verified team/bundle ID. Check the actual profile's
expiry; do not assume a universal seven-day or one-year lifetime. Preserve saves
and container contents before removing/replacing an installation.

**Source checks before a local commit:**

```sh
python3 -m unittest discover -s tests -v
node --check web/check.js
for script in scripts/*.sh; do bash -n "$script"; done
# Stage specific original source/documentation files, then:
python3 scripts/audit_git.py
git diff --cached --stat
git diff --cached --check
```

The hook audits the index, including force-added files. Still review the staged
diff yourself. Never commit `.local/`, game files, generated engine code, screenshots,
profiles or IPAs. Do not push those files to a remote or use cloud compilation.
The helper scripts and this guide are the reproducible source deliverables.
