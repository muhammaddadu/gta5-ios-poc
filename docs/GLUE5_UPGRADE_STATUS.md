# Integrated app status — 12 October 2026

The Glue5 runtime update is signed and installed over the existing GTA V app,
using the same bundle ID, Apple team and on-device data container.

## Confirmed on the phone

Version 1.1, build 2 was exported and installed successfully. The owner confirmed
that the 3D world, movement/camera controls, sound and Settings work. Device process
inspection also confirmed GTA was running. This is gameplay validation, not a
sustained performance benchmark.

The owner then reported missing Playground and other mode choices. Investigation
found the pinned Glue5 host hard-coded engine start mode 1 (Story). The original
adapter now restores a persisted home-screen selector for Story (1), Playground
on the GTA V map (2), and Playground on the test map (3). These numbers follow the
existing engine input contract. Version 1.1, build 3 contains this correction. Its ARM64 build, archive, strict
signature verification, IPA export and installation passed. Selector visibility
and Playground gameplay are awaiting the owner's device check. The test-map
mode is available but has not been validated on this phone.

## Implemented

- Pinned Glue5 revision and Rust compiler, original GTA app identity/icon.
- Existing Documents/data, Documents/shaders and Documents/userdata compatibility.
- Low-memory first-launch profile and approximately 640-line initial rendering.
- Glue5 analog touch/gamepad input, settings, native text entry, MetalFX spatial
  scaling, pipeline caches and frame pacing.
- Original minimum 44-point button hit areas, readable storage status,
  manifest-gated readiness and restored mode selection.
- Explicit exported version/build metadata rather than XcodeGen's default 1.0/1.

## Verification and private outputs

- Device ARM64 compile, archive, strict signature verification and IPA export passed.
- Sixteen repository tests passed, including mode propagation and adapter idempotence.
- Actual modified Rust compatibility tests passed for modern/legacy folders,
  missing-manifest rejection and minimum touch targets.
- Original IPA retained: .local/dist/export/GTA.ipa.
- Updated IPA: .local/dist/glue5/export/GTA.ipa.
- Save backup: .local/upgrade-backups/userdata-before-glue5 (15 files).
- Private build/install logs: .local/glue5-export-versioned.log,
  .local/glue5-install-final.log, .local/glue5-modes-build.log and
  .local/glue5-modes-install.log.

The earlier keychain signing failure is resolved; a fresh signing attempt succeeded.
A launch attempt while the phone was locked failed before starting the app; the
owner subsequently unlocked/opened it and confirmed gameplay.

Long-session temperature/frame consistency, real controllers, save/reload,
background/foreground behaviour and full mission coverage remain untested for the
new runtime. The browser server remains stopped. All third-party code, assets,
builds, logs and signing material stay ignored under .local/. Only original source,
tests and documentation are published to the owner's GitHub repository.
