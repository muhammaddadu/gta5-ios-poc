# Duo build prepared — 31 October 2026

Version **1.1, build 4** compiled for iPhone ARM64, archived, development-signed
and exported using **Xcode 27.2 / iOS SDK 27.2** on macOS 27.2. Both the archive
and the app extracted from the IPA passed strict signature verification. The
exported ZIP passed integrity validation.

Private prepared output: `.local/dist/duo/GTA-Duo-1.1-build4.ipa` (40,578,175 bytes).
The standard latest output is `.local/dist/glue5/export/GTA.ipa`. The original
baseline IPA remains `.local/dist/export/GTA.ipa`.

Implemented: full-window landscape scene, portrait scene above a lower touch deck,
controller-driven reclamation of the full window, live-window back-buffer resizing,
readable portrait home/settings, minimum 44-point settings/button targets,
30 FPS initial mobile cap, MetalFX and low-memory scene workload limit around
1.5 million pixels. New mobile settings start with 80% touch opacity; existing
saved settings remain adjustable and are not overwritten automatically.

Checks passed:

- 17 repository tests.
- 20 native UI/input/settings tests using the actual modified modules with
  synthetic platform/input seams; simultaneous sticks/action, quick triggers,
  layout-transition release, target sizing and scrolling covered.
- 9 resize/presentation/workload checks, plus 2 layout/touch compatibility checks.
  Some geometry tests intentionally overlap between these harnesses.
- Pristine pinned checkout produces the same Rust files as the validated checkout;
  repeated application preserves their bytes.
- Native control/page vector output inspected at portrait/landscape/compact sizes.
  Preview scenes are synthetic and are not gameplay evidence.

**Duo installation is blocked by Apple's device-registration quota.** The intended
phone is connected, with Developer Mode and Xcode 27.2 developer disk image
services available. The owner signed back into the intended Apple account and
Xcode confirms it, resolving the earlier `No Accounts` failure. The targeted
build compiles, then Apple rejects provisioning with:
`Your development team has reached the maximum number of registered iPhone devices.`
Xcode currently exposes only a Personal Team for this account. The existing
profile excludes the Duo, so no install or game-data transfer was attempted.

The owner must resolve membership/capacity on the intended account, or select a
different authorised signing team with capacity, before a fresh targeted build
and export. Account/team changes may require a new bundle identifier; preserve
any existing populated container and saves. Apple explains
[personal-team membership](https://developer.apple.com/help/account/basics/about-your-developer-account)
and [registered-device limits](https://developer.apple.com/help/account/devices/devices-overview/).
For program teams, disabling an old device does not free an annual slot.
The prepared IPA is not provisioned for this phone.

Physical fold transitions, thumb comfort, sustained FPS/temperature, actual Duo
gameplay and save/reload still require the phone. No such results are claimed.
The earlier confirmed gameplay below applies to the original iPhone and older
build, not the new Duo candidate. No phone assets were changed in this preparation.

See [Duo experience and review](DUO_EXPERIENCE.md) and [Duo setup](IPHONE_DUO.md).

---

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
