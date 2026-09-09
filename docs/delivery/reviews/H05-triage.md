# H05 Windows integration review packet

Base187db42; imported Mac source5366789. Main remains unchanged. Mac metadata
reports six arm64 gates passed and a separate amd64 emulation failure. Raw Mac
artifacts have been requested; they are not presently available in this worktree,
so cross-host verification is pending. Do not imply hashes of absent files prove
runtime behavior. Native Linux and Intel Mac remain separate untested lanes.

Local checks: seven WSL shared launcher/data contracts passed in11.712s, including
ineffective advisory locking and owner-token cleanup; existing asynchronous Popen
ResourceWarnings retained. Node host-helper test passed1case when invoked directly.
The initial `node --test` invocation failed to spawn a subprocess under the Windows
sandbox (EPERM), not a failed helper assertion. Direct invocation executes the
same node:test case. Docker context11 exports committed5366789 using the unchanged
amd64 package lock. Build/test evidence is recorded when terminal.

Budget: one H05 critique and at most one focused follow-up, Codex medium600s,
independent of the already closed H04 checkpoint. No H05 review call used yet.

All six Windows host gates passed on committed5366789/image
sha256:955da12afe334d2c8da1fc8f91ef8373cd680afd5ec8831671bef7dcdeba73ce:
startup8321252, browser8336750, failures8379734, restart8388130, lease8409053,
audio8437206 with renderer8444024 (timestamps prefixed178895). Every report and
hash is in references/H05-windows-evidence.json. Both120second audio windows
passed with zero unintended underruns,5,347,968/5,821,056samples, p95148.5/144.4ms.
Earlier latency values remain retained; no interactive/ceiling claim. The
profile-selection unit test also passed. All native/browser runners are terminal.

The user confirmed the Mac artifacts remain on the other machine and asked
whether they are necessary. Clarified that seven JSON reports suffice for initial
independent verification; full logs/audio are only needed if inconsistencies
arise. Windows/code review proceeds without pretending Mac evidence was inspected.

Review01a08641-8f92-7152-9ac6-1bd3809feb98 returned three majors. Accepted:
(1) requested build target architecture is not enforced; require BuildKit's
TARGETPLATFORM plus runtime dpkg architecture to match the selected lock, with
actual mismatched-build rejection and matching-profile acceptance.
(2) JACK diagnostic timeout is not startup evidence; separate detached container
startup, require activated JACK client connections with advancing frame time,
observe bounded continued operation, and explicitly stop/retain owned containers.
Regression faults must reject Docker startup timeouts and absent JACK clients.
(3) Mac independent evidence verification remains pending. It may be completed
where the reports reside on the Mac; no full audio/log transfer is required for
initial JSON report verification. No missing file is treated as verified here.
One focused follow-up remains after fixes/evidence; no second full branch pass.

Architecture baseline reproduced on Windows: context11 exported amd64 source5366789
and `docker build --platform linux/arm64` succeeded, producing image
adf34715d2eec6af14c0a9f1df8fd7bb3f93c15ab78ec2182cf29be24729d75c labelled arm64.
Retained log h05-wrong-platform-baseline.log; never use this diagnostic image as
an accepted runtime. Both Dockerfiles now enforce TARGETPLATFORM/runtime dpkg
architecture before apt, and the inventory verifier compares against lock.platform.
Three focused architecture tests pass. JACK timeout/no-client rejection tests
pass. First real diagnostic9469263 failed on mixed JACK stdout/JSON, remains false;
explicit prefixed JSON result parsing fixes the reporting boundary. Native rerun
is live; no passing claim yet. Build mismatch/correct profile tests follow.

Architecture rejection now observed in actual Docker context12: the first RUN
expands to `test "linux/arm64" = linux/amd64` and exits1 before apt. Its log and
expected-rejection record are retained under artifacts/docker/h05-wrong-platform-*
and h05-platform-rejection.json. A matching linux/amd64 build is in progress.
The corrected JACK diagnostic passed all six real variants in
artifacts/docker/jack-emulation-1788959591165/report.json: seven activated client
connections with advancing frame time per variant, ten-second observation windows,
all final JACK exits0. Prior mixed-output failure9469263 remains false. Two fault
tests prove Docker timeout and running-container/no-JACK cannot pass. Runtime DSP
and the shared launcher/lease code are unchanged since six Windows host gates.

Matching amd64 image built successfully fromfd82a09:
sha256:1f777ecdd4a491afc63988c57bf6a153c5f79b93222c3e5d7e2a8aa1336a4794.
Native cancellation/data reopen/normal shutdown passed in startup-cancel9926606.
H05-fixes-evidence.json identifies actual positive/negative build logs, unchanged
failed diagnostic, corrected live diagnostic, source tests and native smoke.
No native runner remains active. Focused follow-up now owns only the two code
fixes; the Mac-side report verification remains an explicit unclosed gate.
