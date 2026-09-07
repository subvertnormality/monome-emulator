# Controlled-time admission investigation

D18 brings C16 forward for the Mosaic-owned campaign. Status: source inspection,
not an implemented or validated clock adapter. Generic public Session client
passes a native non-Mosaic MIDI probe (80 exact emissions) at
`artifacts/public-client/caf8c787e58b407bb37f71701a489c54`.

Inspected pinned runtime: `.runtime/builds/da993410f493edec/norns/matron/src`.
These observations identify seams, not permission to replace musical scheduling.

| Source | Observed implementation | Required controlled-time proof |
|---|---|---|
| Native clock time | clock.c:29 uses jack_client_get_current_time; references interpolate beat from time and beat duration | Provide one declared clock time source, preserve reference/reset/tempo semantics; retain real time unchanged |
| Coroutine scheduler | clocks/clock_scheduler.c polls every1ms, SYNC uses strict `beat > target`, SLEEP uses `time >= target`; next beat uses FLT_EPSILON | Extract a step/next-deadline seam without rewriting scheduling rules; explicitly resolve boundary epsilon and distinguish reference behaviour from intended musical time |
| Internal tempo clock | clocks/clock_internal.c has a24-ticks-per-beat thread with relative clock_nanosleep and drift correction | Drive the same reference update logic from controlled deadlines; no concurrent wall-clock reference updates in D |
| Metros | metro.c uses CLOCK_MONOTONIC and absolute nanosleep | Controlled metro deadlines must enqueue the same native events; verify resize/restart/cancel, callback registration and simultaneous expiration ordering |
| Lua elapsed/wall time | util.time calls _norns.get_time; os.time/date are separate | Bind all declared time reads coherently, including autosave and debounce; expose unsupported calls explicitly |
| MIDI/capture | emu_bridge.c stamps CLOCK_MONOTONIC | Include logical emission time in D while retaining a distinct real wall-time diagnostic; preserve full native sequence and source identity |
| Other clock sources | clock.c dispatches internal/MIDI/Link/Crow | Admit internal and injected-MIDI clocks only after independent probes; no silent fallback for unadmitted Link/Crow sources |
| Supporting services/mods | SC/JACK services and mods may have additional clocks/OSC callbacks | Inventory mod paths before D admission; fence/barrier completion cannot ignore musical callbacks still arriving from wall time |

Proposed next experiments:

1. Add a new isolated native patch/build candidate. Never edit the verified build
   cache in place. Introduce source-neutral scheduler/metro step seams with the
   real-time threads retaining identical callers and logic.
2. Specify `advance` as repeatedly handling the earliest due deadline, draining
   its native event consequences and any newly scheduled same-time work before
   acknowledging quiescence. Bound work and detect runaway zero-delay cycles.
3. Probe sleep/sync/metronome interleavings, cancel-after-queue, tempo change and
   reset at boundaries using two independent generic scripts before Mosaic.
   Existing native `clock.sync` strictness is a named comparison dimension; do not
   silently introduce one pulse of musical shift or call it acceptable jitter.
4. Compare exact semantic MIDI/frame/grid output with independently specified
   rational event tables and E results. Three D repeats establish determinism,
   not correctness. Clock barriers must also make rendering observably complete.
5. Add D capability/time metadata and P5 review before admitting campaign cases.
   Retain all E/R timing gates and explicitly report any unsupported source.

The current API has no `advance` action. A requested D test must fail capability
admission until these proofs and implementation exist. Testing Mosaic in E can
continue independently; the full musical-timing campaign cannot be declared
complete while its required D capabilities are absent.

## C16 first executable seam (2026-09-07)

`scripts/prepare_clock_step.py` now generates an isolated scheduler-step candidate.
The verified runtime cache and dependency lock remain unchanged. The real-time
thread calls the extracted body at its existing1ms cadence; an external driver
can initialize the same table without creating that thread. Controlled time is
still unavailable until the full driver and all required time sources are wired.

`tests/scheduler_step_contract.py` compiles the original and candidate C sources
against one boundary harness with undefined-behaviour checks. Both pass identical
literal expectations for sleep/sync strictness, fractional offset continuation,
cancellation, same-deadline slot ordering, zero sleep, rescheduling, reset and
capacity/reuse. Evidence: `artifacts/c16/a2399992daad4c178d1efbc7e72807a3/manifest.json`.
This is a native boundary test with clock/event-sink control, not Mosaic workflow
acceptance and not a complete native runtime or determinism proof.

Next: expose pending scheduler deadlines without mutation; connect shared logical
time, internal24PPQN updates and metro deadlines; drain native event consequences
before advance acknowledgement. Then generic real-runtime probes and Codex-only
P5 review are required before any D-mode Mosaic admission.

Pending-deadline inspection now returns separate sleep and sync minima without
mutating scheduler state. Final source-bound differential evidence (including
compiler commands, binary, generator and candidate hashes):
`artifacts/c16/b47fc3d2e0e74ce0aed10b7be517e551/manifest.json`.
No scheduler seam has yet been installed in the production runtime lock.

## Internal clock and metros (2026-09-07 continuation)

Previous execution produced verified scheduler evidence; this continuation makes
further source and executable-test progress. There are no active test runners.

`prepare_internal_clock_step.py` extracts one shared native reference publication
body and adds external initialization plus an atomic tempo snapshot. The native
thread keeps its sleep/drift/catch-up logic and the tempo snapshot from before the
sleep. The compiled original/candidate test executes the real thread loop through
controlled clock/sleep boundaries, including mid-sleep tempo change, restart,
suspend/jump, stop and tick counts past32 bits. Evidence:
`artifacts/c16/0df021d7234a4cbb9d61040534f8789e/manifest.json`.

`prepare_metro_step.py` shares native stage/count/event-post logic between the
production loop and external deadlines. Candidate external mode is enabled before
any metro starts. Pending period changes retain the already scheduled deadline;
future intervals use the native float-to-nanosecond conversion. Equal-deadline
external metros use ascending ID. Restart replaces a pending deadline and cancel
prevents future posting; already posted events remain queued for native dispatch.
Original, modified production-loop and external-loop compiled cases all pass:
`artifacts/c16/b4529ef8b6ed455085f9d1405cfa0b64/manifest.json`.

These are isolated source candidates, not installed runtime modifications. The
remaining integration must share logical time across clock interpolation,
util.time and os.time/date, initialize native components in external mode, advance
to each earliest deadline and drain bounded native event consequences before
acknowledgement. It must also account for redraw completion and reject unsupported
time sources. Zero-progress/runaway callbacks must fail a bounded advance, never
hang or report success. Generic full-runtime probes and Codex-only P5 remain
required; no D capability or completed C16/M5 is claimed.

## First full-native experimental integration

Candidate generation/build helpers now compose the clock seams, an atomic logical
clock, early Lua wall-time binding, bounded native-event dispatch and a framebuffer
fence. The new native advance command acknowledges only after draining its own
consequences; it does not enqueue an acknowledgement that its drain could consume
early. Emission packets retain wall timestamps and separately carry logical time.
Explicit Python Session opt-in selects an isolated experimental installation.
The verified default lock/installation is unchanged.

Local candidate: the ignored `artifacts/c16/current-candidate.json` locator.
Patch recipe/provenance: `artifacts/c16/integrated-01/`.
First full-native probe: `artifacts/c16/f2a3c363ed8b4168a978a321370e4049/manifest.json`.
Three fresh repeats: f67bb5774f2d4fbfb51b3a14fa09d8aa,
253c40b5b3384c589ece602b866d0938, 66f4ca944e5f45d0aaee3ffc68d867e3
under artifacts/c16. Each asserted the same literal MIDI sequence/logical times,
frozen time, exact sleep boundary, strictly-after sync, util/os time coherence,
LED changes and framebuffer propagation.
Second generic full-native probe cf140c923294469b8e3a183a288abe69 passes cached
wall/date binding before script init, same-time child callback quiescence,
cancelled clock/metro silence and expected runaway work-limit failure.
Unchanged public client probe6515534b53dd406c920879c7079f16fb passes80 emissions;
all3 unchanged real-time clock tests pass (37.172s). Existing process-handoff
ResourceWarnings remain the already recorded C11 obligation.

Still unadmitted: P5 has not run. Other clock sources are explicitly rejected in
this candidate; their required controlled-input coverage remains outstanding.
Required next work includes source-change/tempo/reset fault probes, precise
Mosaic musical timing diagnostics, complete time-source/mod audit and bounded
Codex review. Frame-change smoke is not complete screen-semantic coverage.

