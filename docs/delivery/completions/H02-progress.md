# H02 progress: official Maiden and persistent sessions

H01 merged9c67326 before H02 execution. Main native desktop lifecycle passed10
at main artifacts/audio/desktop-20260908-224000/report.json. Main's concurrent
state.json remains SHA25614f3157de699e4d3fa946b3215a82ecc8be0be09333f816983ce9186adabb990.

Implement the mandatory H00 persistent-dataset prerequisite first. Keep fresh
session data default; add explicit --reopen-data for marked launcher datasets.
Metadata schema1 includes independent dataset UUID and canonical code-root plus
relative entrypoint mapping. Edited code remains allowed; mapping changes fail.
Hold a POSIX file lock in the session server for its full lifetime, acquiring
before NativeBackend writes startup files. Reopen refuses seeds and unmarked
paths. Existing generated system.state/system.mods/system.kbd_layout are the
only launcher startup rewrite allowlist; app files remain untouched by launcher.
No system daemon, arbitrary directory adoption or user-project replacement.

Acceptance before Maiden uses a disposable generic native script to save a
counter via K2 and emit its loaded value via MIDI on K3. A new default dataset
must start fresh; explicit reopen after stop must recover the counter without
reseeding. Concurrent attachment fails before native launch; stop releases lock.
Unmarked directories and mismatched mappings fail explicitly without writes.
Then integrate separately pinned official Maiden with the H00 navigation patch,
owned Lua/SC relay and explicit restart recovery; actual browser editing and
REPL/isolation tests remain mandatory. No default runtime promotion.

Native dataset proof passed at artifacts/datasets/native-20260908-224444/report.json:
save2 through K2, contention rejected before native launch, fresh dataset0,
reopen2, native save3, second reopen3, unowned directory unchanged, mismatched
mapping and reseeding refused. Every successful session closed with normal
service exits and absent PIDs. Implementation remains uncommitted/pending H02
integration review; official Maiden is not integrated yet.

Actual interpreter premise passed: artifacts/maiden/stdin-ade53e8d68b742a08463e4fbb8df74e9.json
and that session's native logs. The owned native subclass changed only sclang
arguments from daemon -D to -i emacs; actual matron newline and SC ESC-framed
commands both printed distinct markers. All native processes closed normally.
This is a framing premise, not Maiden/browser acceptance. Reproduction probe is
.runtime/maiden-stdin-probe.py and will become a generic integrated test.

Optional builder scripts/build_maiden.py uses official2e64f7d source, separate
GPL patch directory, checksum-pinned Go1.16.15/Node16.20.2/Yarn1.22.22, no global
installation. Build .runtime/maiden-01 currently active (handle63280); inspect
before resuming. Source symlink-navigation patch is separately GPL-attributed.

First optional build maiden-01 produced its Go binary, but Yarn failed on a
core-js2.6.12 tarball socket timeout; direct Python and pinned Node registry probes
succeeded, including the exact tarball. Only owned stalled YarnPID30468 was
terminated after this diagnosis; runner63280 is terminal. A single diagnosed
retry maiden-02 uses network concurrency1,60000ms socket timeout and600sec overall
install deadline; source lock/integrity remain unchanged. Current runner6534 is
active. Next inspect its result before any retry; no third blind build attempt.
Go/Node/Yarn archives were verified against pinned official/published checksums.

2026-09-09: lost build handle6534 confirmed absent, no surviving owned builder;
retained log was at linking. Offline frozen Yarn recovery88731 completed in365.31s,
then frontend build27756 compiled successfully. Finalized owned maiden-02 after
archive equality and reverse-patch check. Bundle maiden-tools-01 additionally pins
WebSockets12.0 wheel (BSD-3-Clause) and hashes every web asset. No lockfile changes.

Integrated Maiden uses an owned Unix socket (real private /tmp directory; initial
NTFS socket attempt failed explicitly OSError95), authenticated launcher proxy,
session-specific HttpOnly/SameSite cookie, token+origin-checked WebSocket relay,
and actual native stdin/output. Host unit operations are explicitly blocked;
owned restart still pending. Initial browser inspection succeeded on disposable
0d0fdda4652a43b99ac6c84c1952d8d1 and that session was closed. Current browser
acceptance37466 uses fresh032823 session and actual navigation/edit/save/run/REPL.

2026-09-09 resumption: all above runners are terminal and owned sessions closed.
Browser032823/033122 failed save without PUT. Diagnostic033657 saved successfully,
then actual Run failed with SC `/n_free Node 1011 not found`: Crone frees the same
engine in overlapping free/load routines. Official norns upstream1d720942 still
contains both uncoordinated routines. Error remains explicit; no filter waiver.
Maiden loads a selected buffer twice before either response arrives; a late
BUFFER_READ_SUCCESS replaces dirty edits. Deterministic delayed-second-response
regression034056 fails the visible dirty-buffer assertion, with original text
restored. Earlier033932 used inappropriate networkidle against polling Maiden;
that test timeout is retained and replaced by waiting for the specific response.

Before admission, extend the separately GPL-licensed official Maiden patch set
with per-resource in-flight read deduplication. Preserve browser-visible changes
under delayed reads and assert saved file plus changed native output. Extend the
identified optional norns candidate with serialized free/load engine operations,
including allocation completion; verify repeated actual script reloads and audio
after reload. Record official base, inspected upstream and removal conditions.
No changes to official engines, no swallowed runtime errors, no default promotion.
Then finish owned restart, SC-error recovery, two-session switching, stale URLs,
audio after restart, cleanup and H02 review before H03. Main remains9c67326;
other worktrees and concurrent main delivery state are preserved.

Patched Maiden build29177 compiled successfully; bundlemaiden-tools-04 records
all three patches and actual assets. Reload candidateengine-reload-01 reuses
unchanged native binaries and identifies modified SC files. Browser035111 passed
navigation, exact save, changed native CC, four reloads, actual Lua/SC replies.
This exposed and then fixed both late-read and first-change-only Ace defects.
After adding the optional restart route, lifecycle035759 passed two-session
counter/REPL isolation, explicit SC error, fresh-generation restart/reopened
dataset, stale URL/token rejection, native browser controls, actual stereo440Hz
continuity/silence and all native/Maiden PIDs reaped. No audio-engine error waiver.

Retained lifecycle035446 assumed one raw encoder tick at default sensitivity2;
the generic fixture now explicitly requests sensitivity1/no acceleration.
Lifecycle035627 successfully restarted but Playwright lost the response body
after navigation; replacement600116a2cecc4a2283566bd75e0f8cb8 was discovered from
restarted.json and explicitly stopped. The test now reads that durable handoff
and discovers replacements even on assertion failure. All those handles terminal.
The 24 top-level tests passed after server lifecycle changes; full contracts
handle45830 still running at this record. Main state changed independently to
SHA2567ef977b2079db0014c45aeca32e895cbdcc61cab98d9cc6561701ac4c481cf34;
this work did not edit it. Final source-bound browser audio/reload, dataset and
contracts checks, H02 admission review and merge remain before H03.
