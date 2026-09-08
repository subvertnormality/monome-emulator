# Audio and peripheral expansion

Authorized 2026-09-08 by the user's "OK get going", following the proposed
audio feasibility slice. This supplements PLAN/ACCEPTANCE/UPSTREAM; the existing
Mosaic MIDI campaign continues independently. Audio and peripheral support remain
experimental until their own evidence passes. No existing release gate is waived.

## Priority amendment — Mosaic first

User delivery gate, 2026-09-08: complete and verify reliable Mosaic audio/device
capabilities (including audible clicks), then commit and merge that first tranche
before beginning broader scripts such as cheat codes 2. The desktop/Maiden/Docker
queue in DESKTOP.md follows both. Merge is authorized; inspect and preserve
concurrent main/worktree edits before integration. Scoped probe passes alone do
not satisfy this gate.

Goal renewed 2026-09-08: deliver a general-purpose monome emulator primarily for
automated testing, with usable PC/browser script playback where feasible. Work
continues in `codex/audio-monitor`; the goal remains active until audio/device
acceptance and broader application profiles have evidence. A working tone is a
feasibility result, not completion. User-reported faint clicks are owned by A01.

A01 next slices: (1) continuous browser PCM rendering with block-boundary and
sample-rate conversion regression tests, explicit starvation/overflow errors;
(2) engine readiness and identified external SC/mod discovery; (3) native audio
capture/injection lifecycle API and generic note/release/velocity/polyphony/panic
contracts. Follow with Crow transport/CV/ii before broad sampler and arc work.
Browser fidelity checks measure rendered output, including continuity of a known
steady tone; frequency/RMS alone cannot establish absence of clicks. Preserve
phase between transport blocks. No manual listening is an acceptance gate.

User steering, 2026-09-08: prioritize audio and devices useful to Mosaic before
broader application support. The other agent owns Mosaic behaviour scenarios;
this worktree owns generic platform capabilities and focused integration probes.

Delivery order after A00:
1. A01: reliable engine readiness/errors, opt-in audio capture/monitoring, and
   loading identified n.b. player mods through the real mod/SC lifecycle. Prove
   note onset/release, velocity, polyphony, modulation, panic and cleanup against
   a pinned player before offering it to Mosaic's external behaviour suite.
2. P01/P02: virtual Crow transport, CV/gates and the actual ii player commands
   needed by Mosaic (including Just Friends setup/note control). Publish explicit
   absent/supported subsets; do not claim downstream hardware sound.
3. Relevant device connection/reconnection and timing boundaries, coordinated
   with the existing MIDI work; preserve the single runtime input path.
4. Broader softcut/recording coverage, arc and full cheat codes 2 workflows.

Mosaic's pinned n.b. core registers MIDI players; other voices are installed mods.
The original A00 candidate includes official built-in engines only. The separate
audio-mod-01 candidate and session-local OSC adapter now have eight measured
audio checks for an unchanged pinned DoubleDecker n.b. mod; see
`completions/A01-nb-player.md`. This is a focused mod contract, not complete
Mosaic audio workflow acceptance or default runtime promotion.

## A00 — Audio feasibility (completed with recorded limitations)

Depends on C00/C02 native runtime evidence. Use the existing Ubuntu 20.04 WSL.
Reconstruct an isolated candidate from the official lock and declared patches;
never change the current installation, app sources, or another agent's sessions.
Remove the explicit non-None engine rejection in that candidate and expose pinned
official engine classes to SuperCollider. Record every experimental change.

Build a bounded JACK input/output probe: inject known stereo PCM, capture actual
crone output to WAV, retain frame count, sample rate, graph connections, callback
errors/xruns and process status. Missing/short capture, service failure, nonfinite
samples and unexpected Lua errors fail. Assertions use independent tones and
signal properties, with documented numerical tolerances. A silence/muted fault
must fail the tone oracle. No listening or physical hardware acceptance.

Through actual native key events, prove TestSine frequency/amplitude changes,
softcut file playback and live-input recording followed by playback. Initialization
can configure probe scripts; actions may not mutate application globals. Separate
startup transients from measured windows, and record the exclusion explicitly.
Real-time only: controlled Lua time is not synchronized DSP time.

Recording acceptance starts from a cleared buffer, disables monitoring and engine
routes, stops/disconnects injection before playback, and requires retained signal
in both playback and the saved buffer. A disabled-recording fault must fail the
same signal oracle after clearing the destination, excluding live-input bypass.
Engine load paths must remain inside the launch-time interpreted-source identity:
copy unchanged official engines under sc/core/engines in this isolated candidate.
A disposable edited-engine identity must be rejected before evidence collection.

Acquire cheat_codes_2 and its pinned submodules as an opt-in isolated fixture.
Attempt unchanged boot; preserve actual errors and inspect transitive dependencies.
A failed boot is useful feasibility evidence, never an application pass. Do not
spoof norns version to bypass a guard: record the official version requirement
and source compatibility separately from the launcher's existing host version.

Outputs: reproducible candidate/probe commands, JSON+WAV evidence with input and
runtime identities, a boot diagnosis, and A00 completion with limitations.
Perform one focused Codex Paranoia scope review (maximum one focused follow-up),
under RUNBOOK's medium-effort/10-minute budget, before admitting expanded support.

## Subsequent cards

| Card | Depends | Outcome |
|---|---|---|
| A01 | A00 | Supported audio injection/capture API, evidence and lifecycle contracts |
| A02 | A01 | Generic engine/softcut/routing/poll conformance and selected fault checks |
| A03 | A02 | Cheat codes 2 sampler and live-recording end-to-end profiles |
| P01 | C02 | Crow serial/firmware host feasibility, explicit supported subset |
| P02 | P01 | CV trajectories, input callbacks, clock and selected ii protocol profiles |
| P03 | C03 | Virtual arc and optional app integration scenarios |

Crow starts with official firmware reuse feasibility, not assumed firmware
portability. ii command correctness does not certify downstream modules' DSP or
electrical behaviour. Each optional profile owns its dependencies and assertions.
Neither Mosaic nor cheat codes 2 becomes a core dependency. A00 completion does
not claim A01–A03/P01–P03 complete or promote the default runtime.

Progress is recorded in audio-state.json to avoid overwriting the active Mosaic
state.json. Review/completion notes link the exact artifacts, including failures.
