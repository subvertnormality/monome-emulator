# Optional native MIDI output boundary extension

This is an experimental partial checkpoint, not runtime admission. Official
norns pin14bbeae8646c6717f6bb44c8cd60250bf94b6042 remains the dependency. No default
lock changes, no Mosaic imports, and no copied replacement clock implementation.

The confirmed Mosaic master bug and rejected independent-coroutine fix are
recorded in the Mosaic branch02b3427. Codex arbitration session
01a0876c-f9b2-7c63-95b0-8afea1324d1f motivates this generic extension. Its concrete
implementation still requires a scoped Codex review.

## Optional patches and contract

`clock-scheduled-deadline.patch` adds scheduled deadline and epoch to the native
resume event. Lua clock.sync/sleep retain observed time as return1; deadline is
return2 (beats for sync, seconds for sleep), epoch return3. Reset/reschedule
increments the scheduler epoch under its existing lock. Already-queued metadata
is immutable. This does not claim queued stale events are globally suppressed.

`midi-output-boundary.patch` adds clock.midi.subscribe_output({before,after}),
returning a numeric handle. cancel_output(handle) removes it and returns whether
it was active. clear_output_subscriptions and clock.cleanup invalidate all.
Callbacks receive (scheduled, epoch, ports, observed), may not yield, and errors
remain visible. Every dispatch snapshots subscribers and output ports, runs
before callbacks, sends the existing native F8 fanout, then runs after callbacks.
Cancellation takes effect during that dispatch; new subscriptions and output
selection changes affect the next dispatch. Each callback gets its own list of
port IDs. No subscriptions means no requirement for new metadata.

## Evidence

`midi-output-boundary-validation.json` retains exact reports and hashes:
native scheduler legacy parity and deadline/epoch tests;8 Lua API scenarios;
Mosaic-free controlled and real-time native probes verifying before/F8/after
ordering, scheduler metadata and cancellation while F8 continues. These tests
do not establish complete transport, musical timing or lifecycle correctness.

Build with scripts/build_midi_boundary_candidate.py --baseline INSTALLATION_JSON
--prior CONTROLLED_CANDIDATE_JSON --candidate-work NEW_DIRECTORY --output
NEW_INSTALL_DIRECTORY. Both inputs are verified. The current baseline must match
the build tool's selected reference. The composer explicitly reconciles the
existing scheduler-step extraction with the additive metadata patch; unique
source assertions protect that reconciliation. Existing installs are preserved.

Run tests/clock_deadline_contract.py and tests/midi_output_boundary_contract.py
with --upstream-checkout OFFICIAL_GIT_CACHE. Run
tests/midi_output_boundary_native.py --install CANDIDATE_JSON --clock-mode
controlled-experimental, then real-time. Full manifests retain source evidence.

## Next required work

Add delayed native delivery and source/epoch/forwarding probes. Integrate Mosaic
using pending/running generations and exact origin from the dispatch, with a
persistent owner for coincident24-PPQN pulses and native scheduling for96-PPQN
intermediate pulses. Test cancellation before onset, rapid Stop/Start, multi-port
routing and source/output changes. Preserve stock-hardware loading explicitly;
do not claim fixed master timing without a compatible native capability. Restore
M-SYNC009 passing in both modes and rerun affected acquisition, recording and
timing cases, full units and Codex review. Broader emulator/manual/final hardening
gates remain open. Remove these optional patches when equivalent official
upstream functionality is pinned and the same conformance tests pass.

## Coordinated output integration checkpoint

The optional candidate04 native boundary API now has a Mosaic consumer. It emits
Start before the chosen F8, owns coincident lattice pulses after F8, and schedules
intermediate96-PPQN pulses using exact deadlines capped before the next boundary.
Stop cancels the subscription/thread; pending/running local Start coalesces while
explicitly reinitialized disabled lattices can start. Stock norns still loads and
uses immediate playback, with an explicit master-phase limitation; the sync fix
is not claimed without the optional native capability.

All14 affected D/R runs,520 existing units and6 adapter scenarios pass. Source
and manifests: midi-boundary-integration-validation.json. Codex review
01a08785-156e-7a81-bc0b-03fed3a76d2e holds acceptance for shared-clock failure on a
subscriber error and stale queued scheduler state across reset. The latter is
reproduced natively: resetting to0 leaves the next deadline at100.5beats.
Resolve these native blockers before admission, then forwarding/multi-port,
rapid lifecycle, gate/wrap/tempo and the remaining external synchronization matrix.
The original defect baseline remains retained; this is a partial candidate.

## Candidate07 review fixes

Queued/running scheduler state is now distinguished. Reset/source changes rearm
waiting resumes and reject stale queued sync delivery; running coroutines rebase
their next sync. Cancellation and sleep independence have explicit C guards.
Original queued-reset failure is retained; native old04 fails and06passes in D/R.
Candidate07 retains the same scheduler source as06.

Faulting output subscriptions are disabled individually. get_output_error(id)
returns a copy of the retained phase/message diagnostic until cleanup; errors are
also printed. Optional on_error(message,phase,id) may clean up but cannot yield.
Its failures are isolated too. Formatting an arbitrary error value is protected
and has a fallback; subscriber and handler unprintable-error tests pass in Lua
and native D/R. Healthy subscribers and F8 continue. Logical output IDs are
snapshotted per dispatch; native vport device bindings remain resolved at send
time, so remapping needs its remaining acceptance tests.

Codex follow-up01a08799-74cf-7b20-8d9e-de45fb8953c9 confirmed queued-reset correction
and identified the formatter follow-up. That exact negative/positive regression
and native D/R checks now pass. Mosaic faults invoke cancellation and existing
Stop cleanup;520units and7adapter scenarios pass. The14-case D/R matrix passed
on06; four scoped Mosaic startup/restart runs pass on07 after cleanup wiring.
See midi-boundary-fixes-validation.json for source-bound evidence and limitations.

The builder now applies upstream scheduler patches before the verified existing
controlled-step extraction. Candidate05's failed build log is retained;06/07
build successfully. No stock/default installation or runtime lock was promoted.
Next: rapid transport lifecycle/direct init/reset, forwarding and multiple-output
routing/remapping, intermediate notes/gates/wrap/tempo matrices, then the other
documented emulator/manual/final hardening gates. This is not full acceptance.
