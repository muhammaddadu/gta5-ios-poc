# Completed local POC — 11 October 2026

**Task 1: Chrome gameplay verified. Task 2: signed IPA exported, installed and
native phone gameplay confirmed by the owner.** The owner requested that the web
server be stopped and then disconnected the phone; further device checks stopped.
This is a working experimental POC, not a complete retail-game compatibility test.

| Check | Measured result |
| --- | --- |
| Mac/toolchain | Apple Silicon, macOS 26.5.2, Python 3.12.10, Xcode 26.4.1; CMake 4.4.4, Ninja 1.13.2, XcodeGen 2.46.0. |
| Acquisition | All 14 pinned release archives downloaded, hash-checked and extracted locally. Windows runtime not extracted. |
| Complete local inventory | All 12,482 game files matched supplied inventory sizes and SHA-256 hashes: 21,158,604,965 bytes. |
| Engine | Build 8b0b5899ed, SHA-256 11ca8d2c04c5e843d18ff4aea4899d72c86973c6b031df334e67c446b2ae83e0. |
| Chrome capabilities | Chrome 155: WebGPU adapter/device, Memory64, shared memory, secure context and isolation passed. |
| Real engine transport | HTTP 206, correct four-byte WASM magic, Content-Range, WASM MIME and isolation headers. |
| Browser gameplay | GTA V map in Sandbox loaded to a rendered 3D world. Keyboard walking verified; overlay sampled about 31 FPS with 720p/30 FPS parameters. |
| Browser shutdown | Owner accepted browser validation and requested shutdown. The workspace's Python server was terminated; port 8000 verified closed. |
| Native build | Patched wasm2c built, all 256 generated engine files and host compiled to device ARM64; engine and Metal libraries linked. Complete UIKit app build passed. |
| Xcode platform fix | Missing Apple CMake toolchain restored; matching iOS 26.4.1 runtime installed. Asset compilation and archive destination then worked. |
| Apple account | The exact account requested by the owner was verified in Xcode. Account, team and bundle ID details remain private under .local/. |
| Signing/export | Apple development profile created; archive and IPA export succeeded. Both archived app and extracted IPA passed strict codesign verification. |
| IPA | .local/dist/export/GTA.ipa, 66,405,871 bytes. Includes compiled game code; no external data/shaders bundled. Never committed. |
| Actual phone | Device inspection: iPhone 15 Pro, iOS 27.2, Developer Mode enabled. The initially stated iPhone 16 Pro model differed from the connected hardware. |
| Provisioning | Profile includes the connected phone and increased-memory entitlement; recorded expiry 11 October 2027 at 22:00:35 Europe/London. This is the observed profile, not a general free-account lifetime promise. |
| Phone data | 5,817 files, 20,945,061,654 bytes: all remote paths and sizes matched local data; no extra remote files. |
| Phone shaders | 6,615 files, 144,792,037 bytes: all remote paths and sizes matched local shaders; no extra remote files. |
| Early missing-data message | Owner opened app during transfer. Manifest was not yet present. After completed copy and forced relaunch, native game started. |
| Phone gameplay | Owner confirmed 3D world, touch controls and sound worked. Native log shows world simulation and input events. |
| Native sampled performance | One early renderer interval reported 59.5 FPS over 596 frames, zero added validation errors and about 2.3 GB app footprint. This is not a sustained benchmark. |
| Tests | Eleven transport, Git-safeguard and inventory tests passed; Python/JavaScript/Bash syntax checks passed. Real native compiler, app build, signing, export, installation and file transfer exercised. |

## Scope and limitations

Local game hashes were fully verified against the pinned upstream inventory. Phone
files were compared by path and size; all remote hashes were not read back. A
published checksum is not a safety or rights certification.

The native log records initial shader-pipeline compilation/skipped draws and one
653 ms hitch. Long-session thermal behaviour, missions, save/reload, shops and
in-game television have not been comprehensively tested. No claim of a fully
stable retail-equivalent port or independently sustained 60 FPS is made.

A phone screenshot was requested through Xcode, but not relied on for completion
before the owner disconnected. Phone gameplay evidence is the owner's explicit
confirmation plus native logs. Browser rendering/movement was inspected directly
and a screenshot saved locally.

## Private evidence and outputs

- .local/verify-inventory.log and .local/verify-assets.log
- .local/browser-gameplay.png
- .local/compile-engine-objects.log, .local/compile-engine.log
- .local/prepare-renderer-retry.log, .local/build-unsigned-retry.log
- .local/export-ipa-unique.log and .local/dist/export/GTA.ipa
- .local/device/data-progress.json and .local/device/shaders-final.json
- .local/device/game-first-launch.log and .local/device/game-final.log
- .local/signing-team.json and the app's embedded provisioning profile

All inputs, archives, upstream checkouts, derivatives, signing material, logs,
screenshots and the IPA remain ignored under .local/. Only original helper source,
synthetic tests and documentation are committed locally. No Git remote or push.
