# Broader-script combined candidate

Stage 1 is merged at `f301e76`. This stage remains in `codex/audio-monitor`,
pending the bounded review and admission. The default installation, user demo,
external applications and concurrent main state are preserved.

Candidate `.runtime/arc-tools-01/installation.json` composes the fresh canonical
`.runtime/arc-01` runtime, existing host-16 Crow and identified capture/monitor
helpers. Official norns stays pinned at
`14bbeae8646c6717f6bb44c8cd60250bf94b6042`. New locally authored runtime patches:
explicit softcut file-read bounds and optional virtual arc transport. Their
base, rationale, source checks, regressions and removal conditions are in
`A03-read-bounds.md` and `P03-progress.md`. No community runtime fork is installed.

Implemented generic capabilities: stereo/phase/render/position/poll acceptance,
explicit logged audio-file failures, isolated audio file/tree imports, optional
absent Crow, configurable bounded native input timeout, four-ring virtual arc
through official native/Lua APIs, public actions and browser LEDs/controls.
Cheat codes is opt-in and unchanged; no application knowledge enters core.

Evidence index (all under `artifacts/`):

| Boundary | Evidence |
|---|---|
| Combined stereo, polls, callbacks, stop/restart and missing-file error | `audio/softcut-services-20260908-200815/report.json`, 11 checks |
| Combined forward/reverse/rate/loop and actual WAV roundtrip | `audio/softcut-sequence-20260908-200944/report.json`, 7 checks |
| Other generic file failures and C++ read-bound sentinels | `A02.md`, `A03-read-bounds.md` |
| Sample/tree import, simultaneous isolation, slow native input | `A03-prerequisites.md`, `A03-persistence-progress.md` |
| Actual cheat codes sampler/reverse/live recording | `A03-sampler-controls.md` |
| Actual saved collection and fresh-session restoration | `audio/cheat-codes-record-20260908-201053/report.json`, 5 checks on combined candidate; earlier sampler pass at `200106` |
| Native arc and two-session isolation | `arc/native-20260908-195446/report.json`, 8 checks |
| Windows Chromium arc controls/render/offline lease/reconnect | `arc/browser-20260908-195938/report.json`, 5 checks |
| Old-runtime rejection, actual native absence/presence | `arc/presence-20260908-200325/report.json`, 3 checks |
| Unchanged cheat codes arc changes actual source playback | `audio/cheat-codes-sampler-20260908-200640/report.json`, 7 checks |

Top-level unittest discovery passes 22 tests. Separate `tests/contracts`
discovery passes 68 tests in 216.797 seconds, exit 0
(`artifacts/audio/broader-contracts-02.log`). That suite emitted Python
Popen ResourceWarnings; sampled named PIDs were checked after completion and
had exited. No native integration cleanup exception was waived. All integration
checks use actual native input and output; generic contracts have no Mosaic
dependency. Negative controls and historical failed recipes remain recorded.

Limits: supported engines/subsets only; no arbitrary-engine, physical Crow/arc,
hardware timing, click-free arbitrary loop, desktop-speaker, Maiden or Docker
claim. Cheat codes attached ii-module startup remains explicitly unsupported;
its baseline uses an absent Crow. The saved-audio stimulus changed from 660 to
600 Hz because the app's 7.99-second recording loop requires integer cycles for
a coherent whole-file tone assertion. Thresholds and xrun rejection did not
change. Review must examine that rationale and the retained failure evidence.

Next: commit the review snapshot, then
one Codex medium ten-minute Paranoia branch review plus at most one focused
follow-up. No default promotion or stage-3 execution before this stage closes.
