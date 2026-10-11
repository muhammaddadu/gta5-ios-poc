# Local evidence — 11 October 2026

The owner subsequently authorised local acquisition for this POC. Downloads,
full inventory validation and native builds are now in progress. This document
will be updated with measured outcomes; no gameplay or working IPA is claimed
before the corresponding acceptance checks pass.

| Check | Measured result |
| --- | --- |
| Workspace | Initially empty; local main branch initialised, no remote. |
| Mac | Apple Silicon arm64, macOS 26.5.2; approximately 266 GiB available before preparation. |
| Python | 3.12.10. |
| Xcode | 26.4.1 (17E202), full Xcode selected. |
| Build dependencies | CMake 4.4.4, Ninja 1.13.2 and XcodeGen 2.46.0 installed with Homebrew. |
| Chrome | Version 155 user agent; basic WebGPU adapter/device creation passed. |
| Browser WASM | Memory64 validation and shared-memory creation passed. |
| Browser isolation | Secure context, crossOriginIsolated and SharedArrayBuffer passed at localhost. |
| Server transport | Eight integration tests passed: full/range/suffix/HEAD responses, isolation headers, plain/gzip batch reads, malformed requests, traversal/symlink rejection, support page. Synthetic data only. |
| Git safeguard | One integration test passed: force-added private game file rejected; staged source allowed; symlink rejected. |
| Script syntax | Eleven tests now pass (including inventory corruption/rejection), plus JavaScript and Bash syntax checks. |
| Patched compiler | Pinned wabt with native upstream's atomic wait/notify patch built successfully on this Mac. Upstream compiler warnings recorded locally. |
| Synthetic iOS compile | Original f() → 42 WASM module translated into C and compiled with iphoneos SDK to Mach-O arm64 object. Reproduce with `bash scripts/smoke-native.sh`. |
| Asset acquisition | Local-only release acquisition in progress; first archive installed, exact engine hash confirmed, all 256 C files generated. Full inventory pending. |
| Signing | A Mac Developer ID identity was present; iOS development signing not established. No keys exported. |
| Phone | Intended target: iPhone 16 Pro, owner says latest iOS. Actual iOS version not yet measured; no device available to devicectl at inspection. |
| Browser 3D gameplay | PENDING: complete acquisition and inventory verification first. |
| Dawn/game native build | IN PROGRESS: missing-toolchain integration fixed; renderer and engine ARM64 objects compiling. |
| IPA archive/export/install | NOT RUN: engine absent, iOS signing not established and target phone unavailable. |
| iPhone gameplay/FPS/thermal behaviour | NOT TESTED. No independent performance claim. |

Local support server is available at `http://localhost:8000/__support/` during the
session; restart with `python3 scripts/serve.py` if it stops. It shows missing inputs.
This is a diagnostics page, not a game-loading or gameplay demonstration.

Private evidence: `.local/tests.log`, `.local/prepare-native.log`,
`.local/build-engine.log`, `.local/server.log`, `.local/smoke/` and upstream
checkouts. They are intentionally not committed. The source lock file and
instructions are sufficient to reproduce the preparation checks without a game.

Next: finish acquisition, verify the complete inventory and test actual browser
gameplay. Finish native compilation, connect/provision the specific iPhone, then
archive/export, transfer data and complete device acceptance.
