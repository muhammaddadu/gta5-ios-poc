# Evidence required before marking either task complete

Keep machine-specific reports, logs, screenshots and captures under `.local/`.
Record the exact engine hash, all source revisions, OS/browser versions, hardware,
launch settings, data manifest source and test duration. Record permission
provenance separately. Do not commit personal saved games or an Xcode container.

## Browser acceptance

- Full input inventory verified against a trusted complete manifest. The bundled
  verifier's minimum structure + engine hash alone does not meet this criterion.
- Secure context, isolation, Memory64, shared memory, WebGPU adapter/device checks pass.
- Actual engine four-byte range probe returns 206, correct Content-Range and WASM magic.
- Game loads through to a rendered 3D world, beyond menus/HUD/loading screens.
- Walk, drive, interact with the world and check keyboard/mouse plus sound.
- Play for at least 15 minutes, recording freezes, world/shader faults and tab crashes.
- Save, quit, reopen and verify the save reloads; preserve existing saves if errors arise.
- Try a shop and an in-game television: community reports flag these as possible failures.
- Record measured FPS, launch resolution and mode; a 30 FPS URL cap is not a benchmark.

## Native acceptance

- Engine and Dawn libraries build successfully for device arm64, with exact logs.
- Xcode archive/export succeeds; codesign verifies and embedded provisioning allows
  the target phone and entitlements. Do not substitute ad-hoc Mac signing for iOS.
- Signed app installs on the identified iPhone 16 Pro with the recorded iOS version.
- Correct native-specific Documents layout, all files transferred and readable.
- 3D world, touch/gamepad input and audio work; 15-minute gameplay session completes.
- Record thermal behaviour, memory termination, FPS and visual defects. Stop a session
  if the phone reports overheating; do not disable OS thermal protections.
- Background and foreground transition tested, save/reload tested, cold relaunch tested.

## Troubleshooting

| Symptom | First evidence/action |
| --- | --- |
| Missing game inputs | Supply compatible authorised files; no downloading shortcut built in. |
| Chrome loading percentage stalls | Capture first console error and failed asset request; percentage alone is not diagnosis. |
| WebGPU unavailable | Check Chrome hardware acceleration and `chrome://gpu`; update browser/macOS as appropriate. |
| HUD works, world black | Inspect shader/pipeline error and missing shader files; do not declare gameplay. |
| Memory access out of bounds | Verify inputs, record exact action/stack; not proof of low physical RAM. |
| Native header/library error | Inspect pinned Dawn generated include path and static library; retain logs in `.local/`. |
| Provisioning/signing error | Xcode account, correct iOS certificate, bundle ID, registered device, entitlement capability. |
| App killed on device | Xcode device logs/crash report; determine memory/thermal reason from evidence. |
| IPA exists, app cannot run | Verify signature/profile, deployment version, device install, then assets; an archive is not a test. |
