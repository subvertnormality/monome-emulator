# Automated acceptance contract

This is the release contract for a general-purpose norns/grid development utility,
with Mosaic as its first comprehensive application fixture, not a claim
of electrical or hard real-time equivalence with a norns. All required tests are
automated. No hardware, listening, human screenshot approval, or manual clicking
is required. The browser can be used interactively, but manual use earns no
acceptance credit.

## Scope and runtime fidelity

[UPSTREAM.md](UPSTREAM.md) defines mandatory generic G01–G06 gates and the
official-runtime/app-fixture boundary. Core installation, native API conformance
and generic script loading must pass without Mosaic or its dependencies present.
The A01–A24 suite below is an additional app-level contract, not a core dependency
or permission to special-case the runtime. Runtime APIs and updates come from
official monome sources; app behaviour is never copied into emulator modules.

Run the pinned Mosaic application entry point, actual Mosaic scheduler, native
norns Lua/core libraries, params, and runtime clocks in the real-time lane.
Preserve `testing = false`. Hardware adapters replace devices; they must not
replace Mosaic's musical logic, page controllers, persistence, or event handlers.
Each native norns patch must be small, documented, and covered at its boundary.
The definitive patch list and runtime choice are established by C00/C02.

The first release supports a virtual 128 grid, norns display/keys/encoders/menus,
virtual MIDI input and capture, and all documented Mosaic software workflows.
Physical Crow/Sinfonion actions and n.b. audio engines are excluded. Startup calls
to absent physical devices must get explicitly modelled absent-device behaviour,
not a blanket undefined-function no-op. A capability report names supported,
absent, and unsupported operations. Unexpected unsupported calls fail the run.

Sinfonion's software MIDI output is in scope: capture program changes on a virtual
port named `Norns2sinfonion`; only the physical MIDI-to-module conversion is
excluded. The README's LFO/modulation workflow requires pinned `sixolet/matrix`
and `sixolet/toolkit` mods, installed/enabled through actual norns mod lifecycle.
Both base-MIDI (without optional mods) and MIDI-modulation fixture profiles are
mandatory in the Mosaic compatibility fixture at full release, not installed by
default in the generic utility. Mod audio functionality remains outside this contract.

Reference upstream sources (revisions must be locked by C00):

- `https://github.com/subvertnormality/mosaic` — application, README, tests.
- `https://github.com/monome/norns` — runtime and core API behaviour.
- `https://github.com/monome/libmonome` and `https://github.com/monome/serialosc`
  — official grid integration dependencies/protocol references as applicable.
- `https://monome.org/docs/norns/` — software/control/display documentation.
- `https://monome.org/docs/grid/` and serialosc protocol documentation linked
  there — grid device and transport contracts.
- `https://github.com/schollz/norns-desktop` and
  `https://github.com/winder/norns-dev` — candidate implementation references,
  not evidence that current Mosaic already works.

## Independent oracles and avoiding circular tests

Each scenario has an ID, initial project/config, ordered physical-style inputs,
observation waits, explicit expected outcomes, and a cited oracle source. Sources
are documented musical rules, small hand-derived event tables implemented as
fixtures, or separately tested upstream interface contracts. Do not derive
expected MIDI by calling Mosaic's implementation under test.

State inspection helps diagnosis but cannot replace visible screen/grid and MIDI
assertions. Positive workflows create/edit projects through actual inputs. A
fixture can provide a documented starting project, but bypassing all editing by
mutating Lua globals does not prove editing works. A runtime probe script proves
an API boundary; it does not prove Mosaic workflows.

Do not bootstrap a golden by capturing current output and declaring it correct.
Reference frames may be committed only with a justified expected layout/text and
an independent semantic assertion. Limit image masking to explicitly named
volatile areas; no broad tolerance hiding missing pages or stale screens.
Check both raw framebuffer/LED state and browser rendering of representative
frames, so a correct backend with a broken renderer fails acceptance.

For a baseline Mosaic bug: reproduce it with real inputs, classify emulator vs
upstream defect using a focused runtime contract or independent oracle, and save
a minimal reproducer. Diagnostic baseline tests may record a known failure;
required release scenarios may not pass by `xfail`, skip, or exclusion. Prepare
an isolated candidate Mosaic fix where necessary, with tests and a transparent
patch/revision record. Do not modify the user's checkout or change expected
musical behaviour to match the bug. The release manifest must say exactly which
Mosaic revision plus patch set it supports. Publishing upstream is a separate act.

## Test tiers

| Tier | Purpose | Runtime |
|---|---|---|
| U | Existing Mosaic tests and focused emulator contracts | Mocks allowed where explicit; never release-workflow evidence alone |
| I | Input, device, rendering, persistence, and process boundary contracts | Real norns runtime + small probe scripts |
| E | All required workflow rows below | Actual Mosaic via physical-style controls and virtual MIDI |
| B | Browser renderer and control wiring | Actual browser, actual backend, same event path as E |
| R | Timing, transport, reload, process restart and endurance | Real wall-clock runtime; never virtual-clock-only |
| F | Verify test sensitivity to selected realistic defects | Disposable injected faults; expected acceptance failure |
| D | C16 controlled-time musical correctness and feedback | Explicit controlled-clock backend, cross-checked against real-time lane |

Every required software-workflow scenario must run in real-time E; R is the
timing/endurance subset of real-runtime acceptance. Every A01–A22 family needs at
least one required E or R case in addition to its boundary/unit/fault checks.
A23 is mandatory at WSL release and A24 at Linux release; their platform evidence
cannot substitute for one another. C00's tier assignments may add obligations,
not remove this minimum. `release-check` rejects D-only, mock-only, uncollected,
and entirely skipped families, and any required software scenario lacking E.

For A20, E evidence is the independent real-runtime rerun of the affected Mosaic
workflow suites after each blinded repair/feature exercise (C13 step 5), in
addition to the exercise transcript. For A21, E evidence is an injected error in
the actual running Mosaic coroutine path (C02/C12) with captured runtime trace
and the expected failing runner exit; F proves that a swallowed-error defect is
detected. A mocked backend crash alone cannot satisfy A21. C01's verifier encodes
these meanings rather than accepting an arbitrary E label on a report.

Milestone applicability is fixed here, not selected by whichever tests happen
to pass. Future delivery milestones are not prerequisites for earlier gates:

| Gate | Mandatory scope |
|---|---|
| M0 / C02 | C00/C01/C02 empirical probes and runner/native contracts; not full workflow acceptance |
| M1 / C06 | Defined boot/edit/play/save slice plus device/control contracts; not all advanced workflows |
| M2 / C12 | All A01–A19 and A21–A22 scenarios, including both modulation paths; A20 and platform packaging gates have later owners |
| M3 / C14 | All A01–A23 scenarios on WSL, including C13 LLM proof; A24 is not yet claimed |
| M4 / C15 | All portable A01–A22 scenarios plus A24 on native Linux; retain WSL A23 evidence and rerun affected WSL checks if portability changes affect shared code |
| M5 / C16 | Declared supported D scenarios plus affected E/R regressions; no weakening of M3/M4 scope |

Every milestone also enforces applicable G01–G06 from UPSTREAM.md. The runtime-only
installation test deliberately has no app fixture dependencies; full delivery
verification then acquires the app fixture separately. Missing fixture access
blocks an app compatibility claim, not ordinary generic script use.

`D` supplements `E/R`; it cannot stand in for them and does not gate M0–M4.
D18 brings C16/M5 forward for the Mosaic behaviour and musical-timing campaign. Virtual time must include
every time source used by the supported path, including monotonic reads, clock
sync/sleep, metro and relevant Lua time/random calls, or fail with an unsupported
mode error. `math.randomseed(os.time())` at Mosaic startup must be accounted for.
The real-time lane retains production scheduling behaviour.

## Workflow inventory

C00 expands these rows into concrete scenario IDs from every relevant README
section and source path. C08–C11 implement them; C12 checks that none disappeared.
“All documented workflows” means each software feature section has a scenario,
and meaningful documented options have boundary/interaction cases. A named row
below is a family, not permission to test one happy path and ignore its options.

| ID | Workflow and required positive/negative cases | Observable oracle | Owner |
|---|---|---|---|
| A01 | Fresh boot, no existing data, stable initial screen/grid, reload | Ready state, frame/LED layout, no Lua errors, capability inventory | C06 |
| A02 | Grid coordinates, levels 0–15, multiple held keys, press/release and reconnect | Runtime key trace and raw LED matrix; no stuck held input | C03/C04 |
| A03 | Three keys/encoders, shift combinations, param menus, confirm/cancel, file/text dialogs | Callback order, screen state and resulting public behaviour | C04/C11 |
| A04 | Create/edit trigs, note and velocity pages, remove trigs, page cycling | Grid cells and exact note/velocity event table before/after edit | C08 |
| A05 | Channels, device/channel selection, pattern assignment, merge modes, mute, length and wrap | MIDI port/channel, merged event tables, mute silence, independent channel lengths | C08 |
| A06 | Scale, root, degree, rotation, transposition, octave, masks and chords; quantiser options | Independently computed small pitch tables and chord note sets | C08 |
| A07 | Start/stop, reset options, clock divisions, tempo changes, swing/shuffle | Note/transport ordering, beat-domain phase and wall-clock bounds | C07/C09 |
| A08 | Probability and random pitch/trig options with fixed seeds and boundary probabilities | Repeatable trace, 0/100% boundaries, pitch membership; avoid flaky statistical gates | C09 |
| A09 | Trig locks, trigless locks, slides and wrap options, scale/transposition/octave locks | Notes/CCs/values at defined steps and boundary transitions | C09 |
| A10 | Strum, arpeggio, acceleration, spread, chord shape/velocity/mute-root options | Ordered note-on/off tables, positive durations, documented overlap behaviour | C09 |
| A11 | Song slot operations, repeats, sequence length, transitions, song mode/reset choices | Pattern sequence and boundary events; no missing/double transition | C09 |
| A12 | Live MIDI recording, held-step entry, chords, quantised starts/lengths, record arm/disarm | Replay captured input as expected output; grid/screen shows edit | C10 |
| A13 | MIDI controller mapping, relative binary-offset encoders, ranges/channels/selected-channel mapping | Intended value changes only; wrong port/channel does not alter target | C10 |
| A14 | Device configuration discovery and malformed config handling; CC/program changes including Elektron and Sinfonion software output | Expected MIDI bytes/order; invalid config diagnostic and absence from selectable devices | C05/C10 |
| A15 | Undo/redo and memory operations, change cancellation | Previous and reapplied project behaviour through output and display | C08/C11 |
| A16 | Save/load/new/autosave, params/PSETs/PMAPs, missing/corrupt data, reload/restart | Round-trip MIDI trace and visible edits; original files preserved on failure | C11 |
| A17 | Matrix/toolkit LFOs/modulation and parameter mapping interactions | Both mod paths change actual Mosaic MIDI-device parameters with known shape/range/rate and emitted MIDI effects | C00/C02/C09 |
| A18 | MIDI panic, pending note cancellation, repeated stop/start and disconnected client | No outstanding notes after defined drain, no duplicate active clocks | C12 |
| A19 | Dirty display/grid refresh, page indicators, tooltips, edits during playback | Rendered state updates; seeded stale-frame defect is detected | C04/C12 |
| A20 | LLM reproduce/edit/reload/verify loop on a candidate Mosaic change | Saved input recipe, failing baseline, passing candidate, unaffected regressions | C13 |
| A21 | Error observability: Lua exceptions including coroutine errors, backend death, API failure | Nonzero runner exit and structured diagnostic artifacts, never timeout-as-pass | C01/C02/C12 |
| A22 | Real-time mixed-feature endurance and clock/MIDI ordering | Bounded timing, no lost events, no stuck inputs/notes or leaked sessions | C12 |
| A23 | Automated clean install and execution on declared WSL profile | Inventory complete, browser + runtime checks, host facts identify WSL | C14 |
| A24 | Native Linux portability on declared profile | Same suite and fixtures, host facts identify native Linux | C15 |

## Central thresholds and run budgets

These are initial engineering acceptance targets, not measured hardware facts.
C00 may amend platform-dependent values before implementation using a recorded
probe and rationale. Later changes need the runbook's contract amendment; failed
candidates must not silently select easier profiles.

| Gate | Initial contract |
|---|---|
| Required inventory | Every mandatory scenario for the milestone collected/passed; software scenarios require E, every A01–A22 family needs E/R, both base-MIDI/modulation profiles at full release; zero skips/xfails/unexpected errors |
| Exact data | MIDI bytes/port/channel/event count and grid levels exact; note-off equivalence explicitly normalized only where MIDI spec permits |
| Determinism | 3 fresh-process repeats per D scenario produce identical normalized events and end state with same seed/inputs |
| Clock trace | Logical order and planned beat positions exact in D; compare E/R against independently expected beat positions |
| Real-time timing | At 120 BPM, 10-minute C12 fixture: p99 absolute event scheduling error ≤10 ms, maximum ≤50 ms, final phase error ≤20 ms; timing profile records tick units and quantiles |
| Test capture clock | Timestamp at backend MIDI emission using a monotonic clock, never browser receipt; derive expected times from independent tempo/transport schedule |
| Interactive acknowledgement | Local input receipt-to-runtime acknowledgement p95 ≤100 ms over 200 actions; input ordering always exact |
| Render propagation | Required nonanimated observable update within 500 ms of runtime-applied input, using event/frame acknowledgements |
| Short startup timeout | Ready within 60 seconds after dependencies are built; errors retain logs; one explicit cold-start build is separate |
| Endurance | 10 minutes real-time mixing editing/playback/transport; no lost required events, outstanding notes after drain, unhandled errors, or growing active clock/session counts |
| Recovery | 10 load/reload/reset cycles; no orphan processes, held keys, ports, or notes after cleanup |
| Regression on C14 | All mandatory U/I/E/B/R/F selections once on the release tree; repeat timing lane only after a diagnosed environmental failure; D is separately admitted by M5 and required for the Mosaic timing campaign |
| Routine feedback | Target focused smoke under 60 seconds, targeted workflow under 3 minutes; record slowness but don't hide functional failures |

Tempo/swing/strum comparisons must separate intentional musical offset from
scheduler error. Compute native pulse quantisation and delayed note-off rounding
from pinned ppqn/clock contracts before calculating scheduling error; retain both
unrounded intent and rounded expected times. Source-time MIDI ordering and transport reset tests use the
same documented time origin. No arbitrary sorting of captured events to hide a
race. Environment-limited timing is reported as failure of that supported profile,
not silently retried until one run happens to pass.

The same event-error profile applies to each 45-second fractional-rate fixture
(D20). Before collecting its result, declare every scheduled Note On and Note Off,
the independent unrounded musical intent, its quantised native pulse deadline,
and the transport-to-monotonic origin. Exclude explicitly forced Stop releases
from scheduling quantiles and test them against their input/cleanup contract.
Use nearest-rank p99 (rank `ceil(0.99*N)`) of absolute emission-minus-deadline
error, maximum absolute error, and the last planned event's phase error. The
limits remain 10/50/20 ms respectively. Do not fit tempo or origin to emitted
notes, choose whichever rounded deadline fits an emission, or substitute a
short fixture for the required ten-minute C12 profile. Missing verified deadline
or origin mapping means scheduling conformance is unverified, not passed.

An interval or window compares two emissions: its residual is the difference
of their individual scheduling errors. The event profile does not imply a
pointwise 10 ms window bound or a percentile bound on overlapping windows.
Retain these residuals as diagnostics and check the independently planned
musical intervals/windows exactly. Controlled-time musical checks retain their
existing 2 ns allowance, exact MIDI data/counts, and release-before-retrigger
ordering. Historical failures under the earlier pointwise window oracle remain
failed records; this amendment does not reclassify them.

Fresh boot and existing-autosave boot have separate initial-state fixtures. The
runner observes init-return, live scheduler/redraw clocks, and a first script
frame as readiness; device attachment is a distinct capability. Scenarios seed
device configs before boot and account for the actual autosave/splash sequence,
including its random font draws. Do not demand identical transient pixels across
different startup paths or hide whole-screen differences with a broad mask.
First establish which transient frames are actually rendered: a synchronously
set/cleared autosave flag may produce no splash frame. Assert the measured native
sequence and completion, not a splash that the application never displays.

## Proposed CLI and artifact contract

These commands are deliverables, not commands that exist today. C01 owns their
implementation and versioned schemas; later cards extend the backend capability.
Use `./dev/emu` as the stable Linux/WSL entry point.

```sh
./dev/emu doctor --json
./dev/emu fetch --locked
./dev/emu build
./dev/emu start --profile wsl --script /path/to/code/my-app/main.lua --code-root /path/to/code --data .runtime/session-a
./dev/emu fixtures fetch mosaic --locked
./dev/emu test --suite conformance --require-all
./dev/emu status --json
./dev/emu run scenarios/smoke/boot.json --artifacts artifacts/runs/boot
./dev/emu test --suite workflow --require-all
./dev/emu replay artifacts/runs/<run-id>/manifest.json
./dev/emu snapshot --json
./dev/emu stop
./dev/emu verify-evidence artifacts/runs/<run-id>/manifest.json
./dev/emu release-check --profile wsl --require-all
```

Scenario vocabulary: `grid.down/up`, `key.down/up`, `encoder.delta`,
`midi.inject`, `wait.observation`, `wait.beats`, `snapshot`, `assert`, and
controlled-time `advance` where explicitly supported. Inputs have sequence IDs;
acks distinguish received, applied, and rendered. Frame/LED revisions and MIDI
sequence numbers tie assertions to the action that caused them. API mutation of
application globals is not an action. Optional debug inspection is read-only.

A failure bundle contains manifest, input trace, raw MIDI with timestamps,
raw framebuffer and LED states, browser screenshot where relevant, stdout/stderr,
structured errors, and a minimal replay recipe. Results list each assertion,
expected/actual, and relevant event/frame ranges. Secret or unrelated user-file
contents must not enter the bundle.

`release-check` resolves the mandatory suite from the versioned inventory, not
the tests the caller happens to name. It fails on missing tests, skipped tests,
zero collection, missing artifacts, source mismatch, and any required failure.
Warm caches may speed builds but may not supply stale runtime/output evidence.
