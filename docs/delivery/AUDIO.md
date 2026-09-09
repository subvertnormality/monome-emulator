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

## Tranche 2 execution contract (2026-09-08)

Tranche 1 is merged to main at `f301e76`; A02/A03/P03 are now eligible in that
order. Work remains in audio-monitor; main's independent Mosaic state is not
owned here. Previous goal turn was progress: reviewed implementation and merge,
including main native evidence. No live predecessor runner needs resuming.

A02 depends on the admitted opt-in `.runtime/tranche1-final` build. Preserve its
official pins and patches. Current evidence covers basic softcut mono playback,
recording, and engine/n.b. audio. Missing proof is multi-voice/stereo sample
routing, rate/reverse/loop behavior, waveform rendering, phase/position callbacks
and real amplitude polls used by samplers. Implement generic fixtures first:

1. Generate identified independent stereo test signals in disposable session
   data. Exercise native key/encoder controls; capture actual JACK output and
   assert channel-specific frequency/amplitude, rate changes, reverse sequence
   and stopped silence. Use asymmetric time/frequency markers to distinguish
   actual reversed audio, not just a signed rate or position variable.
2. Capture script-visible phase/position/render callbacks through a generic
   fixture's append-only output ledger. Compare requested positions and rendered
   waveform data with the generated source; check start/stop and no stale
   callbacks after a settled stop. Preserve actual native errors.
3. Inject known channel-specific PCM and assert real input amplitude poll
   response, channel separation, decay to silence, stopped callback delivery and
   explicit restart. Poll values alone never prove audio output; pair them with
   routing/capture assertions. Reject a silent/disabled source using the same
   positive oracle. Verify WAV save/reload roundtrip and cancelled session jobs.
4. Add runtime adapters only for empirically missing capabilities. Do not rewrite
   official softcut, fake poll values, or import application behavior into core.
   Record sample rates, excluded startup interval, tolerances, input recipe,
   runtime/source identity, callback ledger, PCM and cleanup evidence.

A03 uses unchanged opt-in cheat_codes_2 `7134bd5b275ffc650210742715d277b6d8f3b927`
and its locked n.b. submodule. Boot-only evidence is insufficient. Inspect its
native UI paths, then automate loading a disposable sample, assigning/triggering
pads, loop/rate/reverse control, live recording from injected PCM, playing the
retained recording with injection disconnected, and save/reload across isolated
sessions. Confirm real output and meaningful selected-pad/UI observations;
never mutate app globals or edit its source to pass. Generic sample access or
persistence gaps must be solved for any script, preserving user projects.

P03 implements virtual arc through the same native input path used by browser
and automation. Prove relative encoder input, 4x64 LED output and ring addressing,
rotations/levels, disconnect/reconnect and held-input cleanup using generic
fixtures. Then add optional cheat codes integration for its supported arc UI.
No electrical or physical device claim. Do not make arc mandatory for baseline
sampler workflows.

Admission uses one bounded Codex medium/10-minute branch review and at most one
focused follow-up for the completed tranche, per RUNBOOK. Review the actual
changes and false-green controls before claiming broader application support.
Desktop/Maiden/Docker remains queued until this broader-script tranche has its
own working implementation and acceptance evidence.

A03 device-presence finding: unchanged cheat codes 2 on the combined candidate
issues ii module reads when Crow is attached and the write-only host rejects
those explicitly (`cheat-codes-boot-20260908-181345`). Preserve this as an
unsupported Crow-attached profile, not an app patch or a passing boot. Add an
explicit per-session optional-device setting (`crow_enabled=False`, CLI
`--no-crow`) that uses official norns' actual disconnected-device behavior.
Default behavior remains unchanged. Acceptance: no Crow process/PTY and native
connected=false when disabled, honest capabilities, clean shutdown; normal
configured-Crow sessions remain supported. Then run CC2's baseline sampler
workflows without optional Crow. Additional CC2 ii/read/module profiles remain
visible residual scope; disabling Crow is not evidence for those profiles.

A03 sample-access contract: add optional `audio_files=[...]` to the Python client
and repeatable CLI `--audio-file PATH`. Copy selected host files into the owned
session audio root without modifying originals; reject missing files and duplicate
basenames rather than overwriting. Record the copied bytes' hashes/sizes in
session identity and exports. Default sessions remain empty. Use streaming copy
so importing a sample does not load the entire file into Python memory.

Automated acceptance: a generic script opens official `fileselect` at
`_path.audio`; native keys select an imported WAV, real softcut playback matches
its signal, and the selected file is identified. A fresh session can import a
different same-named source without affecting the first session or originals.
Missing/duplicate inputs fail explicitly. Use this generic capability for CC2's
sample loading workflow; never seed its internal app globals to bypass the UI.

A03 short-file runtime fix contract: actual sampler run
`cheat-codes-sampler-20260908-183016` reaches `load_sample`, requests 2.05 seconds
from a 2-second file, and fails at seek frame 96256. Pinned BufDiskWorker clamps
only unspecified durations; explicit mono/stereo read lengths can exceed source
and destination capacity. Official main `1d7209428841bc2b38619c8238ba0d2788bdbe68`
was inspected and retains this omission (source linked in the completion note).
Add a small explicit patch on pinned norns `14bbeae...`: clip explicit read
lengths to remaining source frames and destination capacity, preserving untouched
buffer tails and preserve/mix behavior. Do not suppress genuine IO diagnostics or
change cheat codes. Prove mono/stereo EOF and destination bounds against actual
BufDiskWorker jobs with sentinel tails, then repeat the native sampler flow.
Record patch digest/base/removal condition; remove after upstream has an
equivalent fix and the same tests pass without the patch.

A03 persistence contract: collected recordings live in nested `_path.audio`
directories, while existing data seeds restore only `_path.data`. Add optional
`audio_directory` / CLI `--audio-directory` to snapshot an explicit source tree
into fresh session audio, preserving relative paths and copied-byte identities.
Preflight missing sources, symlinks, non-files and conflicting targets; reject
instead of overwriting or following linked trees. Empty directories may be copied;
existing empty session directories may be reused. Originals remain untouched.
Generic native file-picker playback must work for a nested imported file, with
another session independent. Then restore an actual UI-saved cheat codes
collection and its audio into a new session, load using its own collection UI,
and assert retained PCM. No application-specific path remapping in core.

A03 input-wait finding: a real collection-save callback returned its native ack
after 2.090785141 seconds (`cheat-codes-record-20260908-190758`, native sequence
34), beyond the adapter's fixed two-second wait. Add an explicit per-session
`input_timeout` / `--input-timeout` in the bounded range 0.1–30 seconds, default
2. Carry it through native acknowledgement waiting and the Python client's HTTP
response deadline; browser and automation retain the same native path. This
changes only how long an operation may wait for actual completion, never native
timestamps, clock tolerances, audio metrics or error reporting. Slow native
callback conformance must prove completion above two seconds when opted in,
and explicit rejection beyond the configured bound. Use 10 seconds for the
collection test and retain its measured latency; no swallowed timeout or fake
ack. Include the boundary change in the broader-tranche focused review scope.

P03 scheduling clarification: the card table makes P03 depend on C03, which is
already delivered. A03 persistence acceptance currently waits for a usable audio
capture window under host scheduling/swapping pressure. Arc implementation may
proceed within the same broader-script tranche; persistence remains an open gate
and no desktop/Maiden/Docker work becomes eligible. This refines the suggested
within-tranche execution order, not the user's three-tranche queue.

P03 native contract: optional virtual four-ring arc, official norns Arc Lua and
matron encoder events unchanged. Local bridge input kinds 12/13/14 carry relative
delta, encoder-key transition and connection state. Output 18 carries 4x64 native
LED levels and output 19 connection/intensity metadata. Relative deltas are
bounded to ±127 and ring numbers to 1–4 in the public API (0–3 in native packets).
Keys are an explicit virtual profile capability, not a claim about every physical
arc model. Generic protocol checks reject missing/disconnected devices and
duplicate key transitions; disconnect/release-all releases held keys first.
Official arc LED/all/segment logic owns levels and angular wrapping; there is no
new synthetic Lua arc implementation. Grid routing/intensity remain independent.
Browser rings and automation use the same native events and snapshots. Test
all rings, signed deltas, relative levels, angular segments, key release,
disconnect/reconnect, isolation and old-install explicit rejection before admission.

A03 recording stimulus correction: unchanged cheat codes initializes recording
with `loop_end = end_point - 0.01` (7.99 seconds for the first live region).
The previous 660 Hz stimulus spans 5273.4 cycles per wrap, making a whole-file
single-phase tone oracle inappropriate after looping/overdub. The failed saved
recording and its phase/window diagnostics are retained. Use 600 Hz (4794 cycles
per recording wrap and 300 per half-second pad) for the persistence recipe.
Keep the original RMS and >0.85 coherent-energy thresholds, capture xrun checks,
silence negative control, unchanged app and fresh-session load requirements.
This fixture correction does not establish click-free arbitrary live recordings.

P03 app integration recipe: opt-in `tests/cheat_codes_sampler.py --arc` imports
an eight-second sample with 440 Hz in the first half and 880 Hz in the second.
Use unchanged native file-picker/grid controls to loop pad 2, then turn arc ring
1 to move its playback window between the marked halves. Assert actual captured
pitch and native arc LED changes, then reverse the deltas and assert restored
440 Hz. Baseline sampler and sequence profiles keep arc absent.

Stage 2 review amendment: `input_timeout` bounds the entire native action,
including all implicit key releases. Native timeout is a sticky session failure
because a submitted callback may still complete later; further state/actions
must not claim healthy synchronized input ownership. Authenticated browser
heartbeats update lease receipt independently of the device-operation lock,
so a permitted long callback does not impersonate a network disconnect.
Tests must cover late completion, compound release exhaustion/success and a
real connected browser held input/audio monitor across a slow callback followed
by real offline cleanup. See `reviews/A02-A03-P03-triage.md`.

## A04 — Refresh the combined WSL candidate after H04

H04/H05 available-host work is merged. The completion audit found that the
existing WSL candidate predates H04's captured JACK lifetime fix. Build a fresh
optional candidate from current pinned official sources with existing Crow and
arc flags; attach existing audio/desktop helpers and reuse the separately pinned
Maiden installation. Do not promote or edit the current installation and do not
replace another agent's sessions. This adds no new emulated API or DSP behavior.

Acceptance: verify builder source/patch identities; generic native audio stream
and clean shutdown, generic Crow/arc probes, real desktop sink capture, unchanged
Mosaic audio and cheat codes sampler/arc checks against that same candidate.
Existing external fixtures remain opt-in. Reuse H04's reviewed patch and recorded
baseline failure; new combined-build failures require diagnosis, not a waiver.
Update user setup instructions and candidate evidence. This is integration of
already reviewed code; another cold review is not required absent a new material
implementation or acceptance change. Leave platform-not_run lanes explicit.
A04 additionally verifies official Maiden's generic browser edit/run, Lua/SC
REPLs, rendered runtime audio and exact owned cleanup against the refreshed
candidate, reusing its existing disposable fixture and pinned Maiden build.
