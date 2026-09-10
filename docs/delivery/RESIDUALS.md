# Residuals

| ID | Impact | Disposition | Owner / promotion condition | Reason |
|---|---|---|---|---|
| R01 | n.b. sound engine/audio compatibility | later | Future audio scope requested | Explicitly outside MIDI-only release |
| R02 | Physical Crow, Sinfonion, grid USB and external MIDI hardware integration | later | Future physical-device integration requested | No real hardware needed for this delivery |
| R03 | Exhaustive compatibility certification for every third-party norns script | later | A named additional script becomes a full compatibility target | General-purpose loading and native API conformance are required now; universal audio/hardware/script coverage is not claimed |
| R04 | Physical I/O, temperature and network-manager warnings; service-management side effects | fold:C02 | C02 before product readiness | Native host profile needs explicit absent/unsupported handling and safe process lifecycle |
| R05 | Spike has one grid orientation and one MIDI message-event port | fold:C03/C05 | C03 grid and C05 MIDI conformance | Native boundary feasibility proven; stream/multiport/reconnect contracts still required |
| R06 | Adjacent official update ref not built | fold:C14 | C14 real update/rejection/rollback acceptance | Ref and diff inspected only; cannot claim upgrade compatibility |
| R07 | matrix/toolkit root license files absent | fold:C14 | Packaging; never bundle unidentified fixture source | Separate opt-in source fetch preserves runtime/app boundary |
| R08 | Mosaic adjacent equal pitches emit repeated note-ons with aggregated note-offs; strict counted capture reports remaining note 65 after stop | fold:C12 | A18/A22 panic/overlap package must classify receiver semantics and, if defective, isolate a candidate Mosaic fix before release | Discovered during C06 exploratory E4→F4 edit next to F4. Native trace in `artifacts/c06/api-development/` retains mismatch. C06's independent four-pitch slice uses E4→G4; no tracker relaxation, xfail or release exclusion is permitted. |
| R09 | One Windows browser read failed during simultaneous API/browser native suites; native process remained healthy and isolated browser rerun passed | fold:C12 | Reliability/endurance and concurrent-client checks must diagnose or reproduce/resolve before release | Failed package `artifacts/c06/da15eb28c8ab4c0e8d69a7d18420e19c`; browser request-failure logging added. No uncertain action was retried and no failed package is accepted. Current M1 browser evidence is an isolated run, not a concurrent-browser reliability claim. |
| R10 | Scheduled MIDI previously held the shared observation lock for up to two seconds | resolved:C07 | Separate action serialization allows native snapshots and heartbeats during the wait | Two actual future MIDI requests preserve held input and event order while 14 snapshot/heartbeat pairs stay responsive. Failed scheduling remains explicit in the action trace. |
| R11 | MIDI prevalidation rejects isolated F7 and interrupted partial messages accepted by stock norns | fold:C10 | Native input boundary cases must align validation before full recording/mapping acceptance | P1; explicitly reported unsupported until verified. |
| R12 | Historical build-specific patch generators and spike duplicates remain in source tree | fold:C14 | Remove superseded or unsafe cache-mutating generators before distribution | P1; locked patches are the actual build inputs. |
| R13 | First SIGTERM arriving during native close can interrupt its cleanup loop | fold:C11 | Lifecycle interruption tests must cover close already in progress | P1 follow-up residual; ordinary owned startup failure and stop cleanup pass. |

| R14 | Python warns when the server Popen object is collected after intentional asynchronous startup handoff | fold:C11 | Retain/reap the owned server handle and verify repeated lifecycle cleanup | Native service groups currently stop cleanly; the warning is retained in test logs and must not be confused with proven orphan-free parent-process lifecycle. |

No identified in-scope defect may be put here as `later` if it prevents a required
acceptance row from passing.

R16 — Continuous scheduled MIDI refill: fold:C10/C12. The current one-batch
512-event queue suffices for short handoffs but cannot sustain longer external
clock endurance without a refill/extension mechanism. Add one with bounded
storage and unchanged absolute deadlines; never insert gaps or retime a new
batch to pass the timing tests. Required before long continuous MIDI-clock
acceptance, not waived by the short C16 probes.

R15 — Stopped scale-slot highlight: candidate fixed in Mosaic c2e4376, with
real-time and controlled M-SCALE-003 regression evidence and an explicit
held-lock display guard. Mosaic's candidates/scale-stop-indicator.json records
the isolated three-line patch, baseline failure and passing manifests. The
historical native failure artifacts/c08/7af59ee065a04cd9a23e1404d477c631/manifest.json
remains retained. C12 still owns full A19 coverage and release-tree regression;
the focused fix does not complete the display-refresh family.

R18 — Native virtual MIDI hot-plug: implemented and scoped validation passed on
published branch `codex/midi-hotplug` (runtime/test implementation ae203883).
Locked patch0013 provides native lifecycle, ordered input/output boundaries and
explicit scheduled drops. Generic D/R probes, parser/race baseline fixes and Codex
follow-up passed. Mosaic b9d04ea adds four stopped-panic removal/reconnect scenarios
with eight canonical D/R passes and four existing musical regression passes;
its oracle finding is fixed and reviewed. Evidence: C05-hotplug-progress.json and
Mosaic docs/testing/hotplug-validation.json. These do not close all PANIC-GESTURE,
controlled-time admission or release lifecycle requirements. Automatic approval
review rejected main fast-forward/runtime activation; neither ran. Continue using
the authorised published feature branch directly; do not bypass that rejection.

R17 — Controlled-time feedback cost: fold:C13. The Mosaic M-RANGE-002 sweep
passed in 309.63 seconds controlled versus 121.74 seconds real-time. Its driver
polls snapshots while advancing in 10 ms increments, so logical control does not
currently imply faster feedback. Profile transport/capture and consider bounded
event-oriented waits; preserve complete MIDI capture, exact logical schedules,
observable predicates and fresh-repeat validation. Do not relax timing or
coverage to improve the measurement. Run IDs are recorded in delivery state.

R18 — Observer load inside the constrained envelope: fold:C17. A `/snapshot`
serialises and schema-validates the whole observation, including a 4096-message
MIDI tail and the frame, inside the container's CPU quota. Polled every 10 ms it
consumed ~160 ms (quiet) and ~245 ms (dense) of CPU per PERF-001 run and caused
throttling that the runtime workload alone does not
(`perf-001-poll-10-01` versus `perf-001-poll-500-01`). Constrained lanes now poll
at 500 ms and settle for 1 s after setup. Mosaic PERF-002+ drivers must bound
observer cost the same way (event-oriented waits, bounded or incremental
observations) and record their poll interval; their CPU-per-event figures are
not comparable with an observer-heavy baseline. Extends R17.

R19 — Stall-induced permanent phase loss in the pinned internal clock: fold:C17
(PERF-008). Upstream `clock_internal.c` skips ticks when more than one tick
behind, so any stall longer than about two tick periods leaves every later event
late by a whole number of ticks. Measured under CFS throttling: a 29.6 ms
throttle gave +25.0 ms (3 ticks at 300 BPM/24 PPQN) for the rest of the run, and
28.5/27.6 ms throttles gave +32.9/+22.9 ms. This is stock behaviour, not an
emulator patch; PERF-008 must state it and test recovery against it, and must
not "fix" it by retiming expectations.

R20 — CFS period shapes the proxy: later (decision needed before C17 done).
Docker `--cpus 0.5` is a 50 ms quota per 100 ms period, which permits stalls of up
to 50 ms; a slower CPU runs continuously slower instead. A shorter period at the
same fraction would stall for less, but changing the profile is a contract
amendment with focused review, never a response to a failing candidate. Current
evidence is on the unchanged 50000/100000 profile.

R21 — Runtime queue instrumentation: fold:C17, prerequisite of any PERF-008
queue-recovery claim. The recorder's queue counter covers only scheduled native
MIDI input. Matron's event queue (`events.c` `evq.size`) and clock-scheduler
occupancy need a small tested native patch exposing depth and high-water marks.
No queue-recovery claim is made until this exists.

R22 — Concurrent native session startup: resolved on codex/norns-performance.
Six sessions started at the same instant failed 15 of 18 times (crone abort -6,
matron exit 255) while registering clients with their per-session JACK servers,
which share one per-user shared-memory registry
(`artifacts/reliability/concurrent-startup-01`). A host-wide per-user startup
lock (`src/runtime/startup_lock.py`) held from JACK launch to script ready gives
0 of 18 failures (`concurrent-startup-02`), at ~4.7 s serial startup per
session. The same race hit Mosaic's parallel regression suite on the
codex/midi-clock checkout, which does not yet carry this lock. Promotion: move
Mosaic's emulator configuration onto a line with the lock, or transplant it.

R19 corroboration, 2026-09-10: Mosaic's PERF-002 runner
(`mosaic-behaviour-tests/tests/behaviour/perf_dense.py`, preliminary record
`docs/testing/perf-dense-preliminary.json` there) observed an 8-channel run lose
two whole sequencer steps after a ~333 ms stall with zero CFS throttling — host
preemption on a contended host — leaving every later step two steps late. That
is the same stock skip-ahead consequence, reached through a different stall
source. It stays PERF-008 evidence for the refactor (D23).
