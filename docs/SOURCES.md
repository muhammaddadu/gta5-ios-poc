# Sources and provenance, reviewed 11 October 2026

| Project | Direct source | Assessment |
| --- | --- | --- |
| Browser snapshot | [alihammoud21/playgta5](https://github.com/alihammoud21/playgta5) | README says a compiled snapshot, approximately 21.2 GB, Mac gameplay unvalidated by its author, no asset redistribution licence claimed. Reference scripts inspected locally; no game archives fetched. |
| Archived technical reference | [shadany7824/playgta5 engine investigation](https://github.com/shadany7824/playgta5/blob/main/ENGINE_INVESTIGATION.md) | Reports RAGE symbols and Windows development paths in the binary. These are provenance clues, not a retail-to-WASM recipe or permission. We did not clone its game snapshot. |
| Primary native route | [kalki-kgp/gtav-native](https://github.com/kalki-kgp/gtav-native) | MIT host/tool code; user-supplied WASM/data/shaders; wasm2c → C → ARM64, Dawn on Metal, UIKit. App project inspected locally targets iOS 26.0. |
| Alternative native route | [mempage4k/glue5](https://github.com/mempage4k/glue5) | Rust/wgpu runtime; prepared/re-keyed data required; retail files alone insufficient. Engine hash validation in build script. No root licence found at inspected revision. |
| Compiler | [WebAssembly/wabt](https://github.com/WebAssembly/wabt) | Compiler dependency pinned to native host's documented revision, with native host's atomic wait/notify patch. |
| Renderer | [Dawn](https://dawn.googlesource.com/dawn) | Native host's documented revision and iOS BC-texture patch. |

Exact revisions and engine compatibility fingerprint are in `upstreams.json`.
Third-party source checkouts remain ignored with their existing licence notices.
Original server implementation in this repository follows HTTP and the observed
batch protocol; no upstream game loader, shaders or engine code is committed.

Upstream/community FPS and thermal claims are not our benchmarks. The Reddit
reports in the supplied brief were not needed to establish the local toolchain.
Neither a takedown report nor a source-code-leak allegation is treated as a proven
legal finding here. Conversely, public availability and a checksum do not grant
permission. We found no documented authorised acquisition or retail conversion
process in these projects. The missing build remains a concrete input blocker.

A torrent is a transport mechanism, not a source of permission or compatibility.
We do not supply torrent/magnet links or directions to leaked source code. To
continue this particular native/browser port POC without assuming rights, obtain
permission for the supported compiled port and prepared assets from their rights
holders, or use a reproducible port with a demonstrated lawful input workflow.
Keeping derivatives out of Git prevents redistribution through this repository;
it does not settle the legality of acquiring or using the inputs locally.
