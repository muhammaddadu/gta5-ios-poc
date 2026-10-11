# GTA V app upgrade using Glue 5

[Current validation and signing status](GLUE5_UPGRADE_STATUS.md).

This upgrade integrates Glue 5 into the existing GTA V app identity. It retains
the bundle identifier, display name, original blue icon and on-device container.
The original working IPA stays at `.local/dist/export/GTA.ipa`; the updated output
is `.local/dist/glue5/export/GTA.ipa`. All third-party source and game derivatives
remain ignored under `.local/`.

## Features and mobile defaults

- Virtual gamepad touch controls: analog movement/camera, controller prompts and
  aim assist through the engine's pad input, plus real controller support.
- In-game settings for controls, opacity/size, frame rate, scaling, VSync and memory.
- MetalFX spatial scaling and explicit Apple frame pacing; 40 FPS offered when
  the display supports it. This is not frame generation or temporal upscaling.
- Native text-entry keyboard, adaptive control visibility and safe-area placement.
- Pipeline recording/prewarming and a capped resource heap from Glue5.
- Original integration changes: 44-point minimum button hit targets, lower initial
  mobile scene resolution (about 640 lines, quantised render scale), low-memory
  mode initially enabled, GTA V home branding and readable device-local file status.
- Play requires the data manifest and shader index. Missing/incomplete input has
  a start screen and can be rechecked when returning to the app.

Settings remain adjustable. These defaults target the tested iPhone 15 Pro and
avoid assuming a peak frame-rate sample is sustainable. Graphics quality and
performance still require testing in the updated runtime on the actual phone.

## Existing data and saves

`integrate-glue5.py` patches the ignored checkout at documented compatibility seams:

- Both modern `game/data` + `game/b/<build>/shaders` and existing
  `Documents/data` + `Documents/shaders` layouts are accepted.
- On iOS the default search includes Documents, and saves/settings remain in
  `Documents/userdata`, the original app's location.
- No data folders are moved, deleted or copied by the compatibility layer.
- The original game files remain unchanged and need no new download.

Install as an update with the **same bundle ID and signing team**. A different
bundle ID creates a different container and loses access to the installed assets.
Do not uninstall the existing app first. Back up its userdata before updating;
our first backup is under `.local/upgrade-backups/userdata-before-glue5`.

## Build and export

Complete the common game acquisition/verification prerequisites in
[STEP_BY_STEP.md](STEP_BY_STEP.md). Install mise using Homebrew:

```sh
brew install mise
cd /path/to/gta5
TEAM_ID="YOUR_EXISTING_TEAM_ID" \
BUNDLE_ID="YOUR_INSTALLED_APP_BUNDLE_ID" \
JOBS=4 bash scripts/build-glue5-ios.sh
```

The script pins Glue5 and Rust in `upstreams.json`, prepares patched dependencies,
checks the compatible local engine, applies the original adapter, compiles ARM64,
generates the private app spec and exports the development IPA. Approve the Mac's
codesign keychain prompt locally if requested; never put its password in a command
or chat. Account selection must be the owner's intended Apple account in Xcode.

The upstream checkout and generated code stay under
`.local/upstream/glue5-integrated`. The output archive is
`.local/dist/glue5/GTA.xcarchive`. The baseline native host and IPA are preserved.

## Update the phone without re-copying assets

First back up `Documents/userdata` from this app with devicectl's `device copy from`
command or Xcode's app-container tools. Keep the backup private. Then install only
the signed updated app:

```sh
xcrun devicectl device install app --device YOUR_DEVICE_IDENTIFIER \
  .local/dist/glue5/GTA.xcarchive/Products/Applications/GTA.app
xcrun devicectl device process launch --terminate-existing \
  --device YOUR_DEVICE_IDENTIFIER YOUR_INSTALLED_APP_BUNDLE_ID
```

The original `install-ios.sh` also supports this archive through `APP=...`, but it
copies data and shaders again. An already-populated container needs only the app
update above. For a fresh installation, use that helper to populate the legacy
layout, which the integrated runtime supports.

Verify Ready on the start screen, open Settings before Play, then test:

1. Touch movement/camera together, face/shoulder buttons, entering/driving a car.
2. Settings gear access during gameplay; touch size/opacity and Auto/Always/Off.
3. Controller input if available, including prompts and switching back to touch.
4. Render scale, MetalFX and frame-rate options; native UI stays readable.
5. World rendering, audio, save/reload and background/foreground behaviour.
6. A longer same-scene run for frame consistency, memory and temperature.

Some graphics changes require restarting the game. Glue5's engine cannot restart
inside the same process; reopen the app where required. First-run pipeline
compilation can temporarily omit draws. MSAA and other upstream renderer limits
remain; integration does not remove those limits.

## Rollback

Retain the baseline IPA/archive and the userdata backup. Install the old signed
app over the same bundle ID to return to the previous runtime without deliberately
removing its container. Preserve a backup before rollback; settings formats differ.
Do not delete or overwrite save files automatically if either runtime rejects them.

## Validation records

- All 14 repository tests pass, including adapter idempotence/drift checks.
- `python3 scripts/test-glue5-compat.py` runs Rust tests against the actual modified layout module verifies
  modern and legacy folders and rejects a missing data manifest.
- iPhone ARM64 runtime compilation passed after correcting SDL's borrowed-path
  return type. Build/signing/device/UX outcomes are recorded separately as they
  complete; a compiler pass is not proof of phone gameplay.
- Private logs: `.local/glue5-build.log`, `.local/glue5-build-retry.log`,
  `.local/glue5-ux-build.log`, `.local/glue5-export.log` and the upgrade backup log.

Runtime attribution: [Glue 5](https://github.com/mempage4k/glue5), pinned to
`c7df60a8390427a73e142685b2438f29b7214908`. Its source stays in an ignored checkout;
only the original compatibility/build scripts and documentation are committed.
