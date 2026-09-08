# A01 progress: engine allocation readiness

2026-09-08; experimental, pending fresh native regression.

`tests/audio_init.py` uses the unchanged official TestSine engine and sends
frequency/amplitude commands from a generic script's init function. It measures
actual 440Hz PCM, sends Stop through native keys, checks silence, then starts a
fresh session. No init command is retried or delayed by the script.

Baseline `artifacts/audio/init-20260908-170451/report.json` reproduced the race
on the second trial after the first passed: `FAILURE IN SERVER /n_set Node 1012
not found`. Failed-start session `8eeeeabbae8e45d68aec50ed6197cd53` retains native
logs and cleanup. The error was surfaced rather than ignored.

Patch base: official monome/norns 14bbeae8646c6717f6bb44c8cd60250bf94b6042.
`scripts/prepare_engine_ready.py` inserts `Crone.server.sync` between engine
allocation and its ready callback in `sc/core/CroneEngine.sc`. The method already
runs inside a Routine. The symmetric free path already performs this barrier.
The patch waits for allocation work submitted to the server before Lua script
initialization can send commands. It does not promise readiness for arbitrary
background routines spawned by an engine after alloc returns.

Official upstream main was checked at
1d7209428841bc2b38619c8238ba0d2788bdbe68; its source still has alloc immediately
followed by doneCallback, without this barrier. The immutable file is retained
at `artifacts/audio/engine-ready-upstream.sc`. Removal condition: an official
runtime update supplies equivalent engine readiness, or a better official
interface replaces this boundary, and the native regression passes without the
local patch. No community fork is used.

Candidate `.runtime/audio-ready-01` snapshots interpreted Lua/SC and references
unchanged remaining runtime paths/binaries. It records the exact patch digest;
the canonical candidate builder uses the same patch function. Default install
and live demo are untouched. Three fresh native init/audio/stop trials are the
next acceptance check, followed by relevant combined-runtime regressions and
admission review before tranche-1 commit/merge.

Fresh evidence `artifacts/audio/init-20260908-170722/report.json` passes all
three independent init-command/audio/stop sessions on audio-ready-01. The exact
patch is tracked at `patches/norns/experimental-engine-ready.patch`. This scoped
regression supports the barrier; it does not admit every possible audio engine.
