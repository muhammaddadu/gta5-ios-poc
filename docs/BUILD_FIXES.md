# Integration fixes discovered on this Mac

## Dawn Apple toolchain omitted by the native helper

`JOBS=4 bash scripts/prepare-renderer.sh` initially built Dawn's host `protoc`
successfully, then failed configuring the iPhone build with:

```text
Could not find toolchain file: "build-tools/apple.toolchain.cmake"
```

The subsequent missing Ninja/compiler messages were cascading errors. Ninja was
installed; the requested file did not exist in the pinned Dawn checkout.
Dawn's own pinned `.github/workflows/ci.yml` lines 309–314 creates `build-tools/`
and downloads `ios.toolchain.cmake` from leetal/ios-cmake revision
`6fa909e133b92343db2d099e0478448c05ffec1a`. The native helper omitted that step.

Our original `prepare-renderer.sh` now performs that exact pinned dependency step
before invoking a local copy of the upstream helper. It also bounds the final
Ninja invocation to `JOBS` because the upstream direct Ninja call otherwise ignores
`CMAKE_BUILD_PARALLEL_LEVEL`. Upstream source is preserved; its helper copy,
toolchain and third-party files remain ignored under `.local/`.

The same iPhone configuration subsequently succeeded and produced `build.ninja`,
and compilation progressed into Dawn/Tint. This is a real integration check against
the pinned dependency and Xcode SDK. A synthetic unit assertion about a filename
would not exercise CMake's cross-compilation behaviour, so the regression seam is
the actual configuration/build command, not a mocked test.

Private logs: `.local/dawn-config-repro.log`, `.local/prepare-renderer.log` and
`.local/prepare-renderer-retry.log`. Completion of the renderer archive and native
host is recorded separately in `STATUS.md` once measured.

## Xcode generic iOS destination unavailable

The engine and Metal libraries both compiled with the iPhoneOS compiler SDK, but
`export-ipa.sh` then failed before app compilation:

```text
Any iOS Device ... error:iOS 26.4 is not installed.
Please download and install the platform from Xcode > Settings > Components.
```

`xcodebuild -showsdks` listed iPhoneOS 26.4, and first-launch status was complete.
`xcodebuild -showdestinations` reproduced the ineligible generic device destination.
The official `xcodebuild -downloadPlatform iOS -architectureVariant arm64` command
was started; it selected Apple's iOS 26.4.1 simulator component, approximately
8.46 GB. Similar generic-device errors resolved by that command are documented in
[this Apple Developer Forums thread](https://developer.apple.com/forums/thread/739798).
Its outcome on this Mac must be verified by repeating `-showdestinations` and the
archive, not assumed from download completion alone.

A direct unsigned `-target GTA -sdk iphoneos` build reached the asset catalogue
compiler and reproduced the component gap more precisely: no matching simulator
runtime was available for SDK build `23E252`. Existing runtimes listed in that error
were other SDK builds. We kept the original icon/resource build and continued the
official matching-runtime installation rather than removing resources to mask it.

## Early phone launch while data is still transferring

The installed app can be opened before the large data copy completes. On this
phone it displayed “Game data not found” while `Documents/data/manifest.json`
was still absent. The correct `Documents/data` and `Documents/shaders` folders
were present; a device inventory showed the data copy was only about 59% complete.

The UIKit shell checks the paths at its initial startup and retains that missing
state. A normal process-launch request can merely bring the existing app forward.
Our install helper now uses `--terminate-existing` after both transfers complete,
so an early launch is restarted and the newly copied paths are checked again.
This changes only the POC app process; it does not reinstall or delete its data.
