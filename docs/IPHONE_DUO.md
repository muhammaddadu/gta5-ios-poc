# iPhone Duo build and installation

Use Xcode 27.1 or later with its matching SDK/device support. Apple documents the
full-display behaviour of the iOS 27.1 SDK and later in its
[Duo preparation guide](https://developer.apple.com/iphone-duo/prepare/).
Check [Xcode's host requirements](https://developer.apple.com/xcode/system-requirements)
before installing it. The Mac used for this POC was updated to macOS 27.2; its
previous macOS 26.5.2 could not run Xcode 27.1/27.2.

## Prepare the phone and build

1. Connect the intended phone by USB, unlock it and trust this Mac.
2. Enable Settings → Privacy & Security → Developer Mode. Restart, unlock and
   confirm Turn On. Passwords and signing approvals are completed locally.
3. Check `xcrun devicectl list devices`, then inspect the intended identifier with
   `xcrun devicectl device info details --device YOUR_DEVICE_ID`. Match identifiers,
   not names: the old Xcode mislabeled the Duo as iPhone 4 and two phones had the
   same name. `iPhone19,4` was the observed product identifier.
4. Verify developer support:
   `xcrun devicectl device info ddiServices --device YOUR_DEVICE_ID`.
   A missing image variant requires compatible Apple device support; enabling
   Developer Mode alone does not resolve it.
5. Follow the asset and signing prerequisites in [STEP_BY_STEP.md](STEP_BY_STEP.md).
   Use the same intended Apple account and team; keep them private under `.local/`.
   Open Xcode → Settings → Apple Accounts and confirm that account is signed in.
   After the Mac/Xcode upgrade, the saved signing certificate was still present
   but Xcode had no signed-in account. A generic archive could use the old profile,
   while registering the new phone failed with `No Accounts`. Complete sign-in
   locally before retrying the targeted build.
6. Build with the intended device identifier so Xcode registers it and updates
   the development profile before making the generic archive. The helper resolves
   a CoreDevice identifier to the hardware UDID required by Xcode, then checks both
   the archived and exported profiles include it:

```sh
TEAM_ID="YOUR_TEAM_ID" BUNDLE_ID="YOUR_APP_BUNDLE_ID" \
DEVICE_ID="YOUR_DEVICE_IDENTIFIER" JOBS=4 bash scripts/build-glue5-ios.sh
```

Check the resulting embedded provisioning profile includes the new phone's UDID.
A successful generic archive does not establish that the new phone is provisioned.
Outputs remain `.local/dist/glue5/GTA.xcarchive` and
`.local/dist/glue5/export/GTA.ipa`. Version 1.1 build 4 adds mobile resizing support.

## Install and copy data

For a fresh phone, use the asset-transfer helper with the new archive:

```sh
DEVICE_ID="YOUR_DEVICE_IDENTIFIER" \
APP="$PWD/.local/dist/glue5/GTA.xcarchive/Products/Applications/GTA.app" \
bash scripts/install-ios.sh
```

The complete local data/shader set needs approximately 21 GB on the phone. Keep
USB connected until it finishes. Do not open the game midway through copying.
For an existing populated app container, install the app alone as described in
[GLUE5_UPGRADE.md](GLUE5_UPGRADE.md); do not uninstall it or overwrite its saves.

## Settings and display transitions

Start with low-memory mode enabled, MetalFX enabled and a 30 FPS cap. Leave touch
controls on Auto, initially at 80% opacity. These are conservative starting settings, not a measured optimum
for this model. Increase frame rate or resolution only after observing a stable
longer session. Native UI resolution is separate from the lower scene resolution. Mobile
low-memory rendering also caps the scene workload to approximately 1.5 million
pixels; the native UI continues to use the complete display. Existing saved
settings are preserved, so review them when updating an older installation.

The compatibility adapter now allows the engine's back buffer to follow changes
in the live window size on mobile. It retains the session's render scale and
memory profile, skips zero-sized windows and clears held game/touch input before
submitting a changed render size. Touch layout already follows the live window
and its safe area each frame. Graphics settings that require a new session retain
that behaviour. Story and both Playground modes remain available.

The Duo adapter supports portrait and landscape. Portrait touch input uses a
dedicated lower deck; landscape and physical-controller play use the complete
window. The Metal presenter and engine use the actual scene region, while UI
remains at native resolution. See [DUO_EXPERIENCE.md](DUO_EXPERIENCE.md) for design
references, acceptance criteria and evidence. Physical fold transitions, every pose,
thumb comfort and sustained performance still require the phone.

Verify on the phone:

- Ready, then Playground · GTA V → Play; world, movement, camera, audio and Settings.
- Fold/unfold while running in landscape; correct scene aspect, touch placement,
  readable UI and no buttons remaining held after the transition.
- Repeat both directions and try a controller if available.
- Observe frame consistency, memory and temperature over a longer session.
- Save/reload and background/foreground behaviour.

Run `python3 scripts/test-mobile-resize.py` after applying the adapter to exercise
its actual Rust resize method with synthetic window/input seams. This complements,
but does not replace, a physical-device fold/unfold test. Keep all generated tests,
logs, game materials and binaries under ignored `.local/`.

## Preview without a phone

After applying the adapter, run `python3 scripts/preview-duo.py` to render the
actual private native touch module against a synthetic input backend. The helper
builds its private Cargo harness under `.local/duo-preview`. It serves only the
original preview page and generated preview results on `127.0.0.1:8091`.

For a platform-neutral geometry preview, install the Rust WASM target and run:

```sh
mise exec rust@1.99.0 -- rustup target add wasm32-unknown-unknown
python3 scripts/preview-duo.py --portable
```

This compiles the original shared Rust geometry for the browser; its drawing and
input simulation are illustrative. The page explicitly distinguishes it from
native drawing/input validation. The city illustration is synthetic, not gameplay.
Neither mode serves the repository, game files or the entire private directory.
Stop the preview with Ctrl+C. The original Chrome game server stays stopped.

## Prepared local candidate

Version 1.1 build 4 was compiled, archived and exported on 31 October 2026.
The local named copy is `.local/dist/duo/GTA-Duo-1.1-build4.ipa`; its manifest,
checksum and signing status are beside it. The build currently uses a development
profile that **does not include the Duo**. Reconnect the intended phone and run
the targeted build command above to register it and refresh signing. The app and
external data transfer then remain necessary; possession of the IPA alone does
not install or validate the game. The phone has since been reconnected and developer support verified, but the
initial `No Accounts` error was resolved by signing back in. Apple then rejected
registration because the team has reached its registered-iPhone limit; Xcode
currently shows a Personal Team. No Duo installation or data transfer has occurred.
Resolve the account's membership/capacity, or choose another authorised team, then
retry the targeted build. See [current status](GLUE5_UPGRADE_STATUS.md).

After `python3 scripts/preview-duo.py --build-only`, run actual native UI/input tests
without a phone using:

```sh
mise exec rust@1.99.0 -- cargo test --manifest-path .local/duo-preview/Cargo.toml
python3 scripts/test-mobile-resize.py
python3 scripts/test-glue5-compat.py
python3 -m unittest discover -s tests -v
python3 scripts/audit_git.py
```
