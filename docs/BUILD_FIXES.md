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
