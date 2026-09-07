# General-purpose monome emulator: staged autonomous delivery plan

You are an execution agent. When implementation is authorized, execute the cards
below in graph order using [RUNBOOK.md](RUNBOOK.md); resume from `state.json`.
Read [ACCEPTANCE.md](ACCEPTANCE.md) before making runtime or test-design choices.
Read [UPSTREAM.md](UPSTREAM.md) for the general-purpose product boundary, official
runtime dependencies, independent app fixtures and update acceptance (D11/D12).
Do not treat this document's proposed commands or unverified premises as existing
implementation. This planning deliverable does not itself start implementation.

## Outcome and current facts

Deliver a general-purpose norns/grid utility that loads external scripts without
a Mosaic dependency. Mosaic is the first comprehensive acceptance fixture: a
developer or LLM can edit Mosaic, reproduce realistic interactions, observe the
screen/grid/MIDI effects, and run automated
regression checks without a norns or physical grid. WSL2 is the first release;
native Linux follows. MIDI only; no audio acceptance. Cover all documented Mosaic
software workflows. No required manual tests, including final certification.
Generic G01–G06 gates are equally mandatory. Passing Mosaic alone cannot establish
the product's general-purpose or upstream-updateability claims.

Planning workspace: `C:\Users\andy\Documents\ChatGPT\monome-emulator`.
Existing WSL distro: `ubuntu-20.04`. The user corrected the earlier willingness
to move distros: use the existing distro first, prove any actual incompatibility,
and do not assume an upgrade is necessary. WSL source placement and container
use are engineering choices subject to empirical feasibility and preserving the
user's development workflow.

Inspected Mosaic revision: `160d1ea7506773e65f298094e11d005dcb568dff`. Its entry
point sets `testing = false`, connects a grid, uses n.b., Crow startup calls,
params, text/file dialogs, timers and coroutine clocks. Its unit runner replaces
the scheduler and other runtime surfaces with mocks and downloads norns libraries
from the latest release. Existing CI uses Lua 5.3. These tests are useful but do
not establish interactive/runtime fidelity. See `upstream/mosaic/mosaic.lua`,
`lib/tests/run_tests.lua`, `lib/tests/helpers/mocks/`, and `.github/workflows/main.yml`
in the local inspection checkout. This is evidence from source inspection, not a
successful boot or test run.

## Architecture hypothesis and boundaries

Prefer a Linux-hosted build of actual norns matron/core, retaining production
screen drawing, Lua loading, params and clocks from pinned official monome sources.
Application scripts are loaded as external inputs. Provide virtual
hardware and an automation bridge at the native device/event boundaries. Run
supporting norns services only as required for faithful startup/control; dummy
audio is acceptable and need not be exposed as a feature. Reuse desktop projects'
approaches or explicit patches on top of an official monome/norns ref; never pin
a community fork as the runtime dependency. Do not copy their compatibility
claims into this project's acceptance report.

The runtime, browser, and test harness share one event path. Browser inputs and
scenario inputs become the same ordered device events. The browser renders actual
framebuffer and grid state. The harness captures actual MIDI emission and obtains
read-only diagnostic state. Real-time operation is primary. Deterministic time is
an explicitly tested runtime adapter (C16, brought forward by D18), not a replacement sequencer or
a prerequisite for WSL/Linux workflow acceptance.

Owned packages:

| Package | Owned contract | Acceptance boundary |
|---|---|---|
| Bootstrap/launcher | Locked sources, platform diagnosis, isolated process/data lifecycle | Clean machine bootstrap, restart and reproducible source identity |
| Runtime adapter | Norns startup, input enqueue, screen capture, absent peripherals | Native API probes and real Mosaic boot without broad stubs |
| Virtual grid | Serialosc/device discovery or supported native grid transport, keys and LEDs | Runtime sees device; grid has correct coordinates, holds and brightness |
| Virtual MIDI | Input/output ports, raw events and emission-time timestamps | Real runtime transport round-trip, independent decoder |
| Automation | Event protocol, scenario execution, observation and evidence | Machine-verifiable results and meaningful failure exits |
| Browser | Physical controls and framebuffer/grid rendering | Browser actions reach runtime and actual runtime output is rendered |
| Clock adapter | Deterministic control of required time sources | Differential tests with real-time runtime and independent musical expectations |
| Scenario suite | Documented software workflow inventory and oracles | Actual Mosaic is exercised and wrong output is detected |

C00 can choose among proven desktop/runtime transport approaches. A broad Lua API
reimplementation is not an automatic fallback: if the actual-runtime route fails,
record the exact obstacle, test the smallest alternative, and amend this complete
architecture contract before implementing dependent cards. Preserve the same
acceptance scope. Do not spend multiple cards building a visually convincing UI
before proving Mosaic can boot through the native runtime.

## Premise ledger

| ID | Claim | Status | Evidence / closing card |
|---|---|---|---|
| V01 | Mosaic has desktop tests and uses mocks that omit runtime interactions | Verified by source inspection | Files above; C00 records full revision and baseline run |
| V02 | Mosaic requires grid, params, timers, MIDI, n.b. and startup peripheral handling | Verified by source inspection, not complete inventory | `mosaic.lua`; C00 enumerates transitive calls/submodule |
| V03 | Existing norns desktop projects can be reused for current Mosaic | Replaced by official-runtime route | C00 selected pinned official matron/crone with explicit host patches; C02 real Mosaic boot |
| V04 | Existing Ubuntu 20.04 WSL can host the chosen runtime | Proven for native startup and script services | C00/C02 builds and runtime packages; no distro change |
| V05 | Virtual grid can connect through real native norns event handling | Attachment proven | C00/C02 native input/LED evidence; C03 full conformance remains |
| V06 | Headless/no-audio startup preserves supported control behaviour | Startup and generic controls proven | C02 both Mosaic profiles, real services and explicit absent-device handling; later full workflows remain |
| V07 | Deterministic time can cover all supported Mosaic time sources faithfully | Unverified | C16 dual-mode probes; required for the Mosaic musical-timing campaign (D18) |
| V08 | All documented software workflows have executable independent oracles | Unverified | C00 inventory; C08–C12 implement and audit |
| V09 | LLMs can diagnose and repair a Mosaic regression from the tool outputs | Unverified | C13 blind, isolated repair exercise |
| V10 | WSL and native Linux pass the same workflow contract | Unverified | C14 WSL; C15 native host evidence separately |
| V11 | Generic native script loading works without Mosaic or its dependencies | Proven for launcher/loader | C02 two generic apps with all installed app fixtures hidden and networking disabled; C04 browser and C14 packaging remain |
| V12 | Official runtime dependencies can be updated without coupling app revisions or growing a fork | Unverified | C00 lock/patch graph; C14 real update and rollback rehearsal, G04/G05 |

Unknowns block only their dependent scope. A plan review does not change a runtime
premise to verified. Do not claim “cannot work” from a failed broad search; inspect
canonical build/API paths and run a small experiment.

## Graph and milestones

Top-to-bottom is a safe execution order. Within a card implement cohesive slices;
the graph does not require parallel agents. Do not create a new orchestration
system or automatically create Codex tasks to run it.

| Card | Goal | Depends | Milestone |
|---|---|---|---|
| C00 | Prove host/runtime feasibility and freeze compatibility inventory | P0 plan review | M0 foundation |
| C01 | Establish automation protocol, evidence schema, runner and launcher shell | C00 | M0 |
| C02 | Run official norns, generic script loading and separate Mosaic fixture | C00, C01 | M0 |
| C03 | Deliver virtual grid through the real runtime | C02 | M1 first usable slice |
| C04 | Deliver screen, controls, browser and input lifecycle | C02, C03 | M1 |
| C05 | Deliver virtual MIDI input/output and timestamped capture | C02 | M1 |
| C06 | Prove boot/edit/play/save workflow end to end | C03, C04, C05 | M1 + P1 review |
| C07 | Add real-time clock contracts, replay and timing measurement | C06 | M2 comprehensive verification |
| C08 | Verify pattern/channel/harmony editing and undo/redo | C07 | M2 |
| C09 | Verify advanced sequencing, locks, modulation and song behaviour | C08 | M2 |
| C10 | Verify recording, mapping and device MIDI interactions | C08, C05 | M2 |
| C11 | Verify persistence, dialogs, lifecycle and project isolation | C06, C08 | M2 |
| C12 | Close workflow inventory; fault, timing and endurance acceptance | C09, C10, C11 | M2 + P2 review |
| C13 | Prove autonomous LLM Mosaic iteration and usable diagnostics | C12 | M3 WSL release |
| C14 | Package WSL2 release and verified official-dependency update workflow | C13 | M3 + P3 review |
| C15 | Deliver native Linux parity with the same automated suite | C14 | M4 + P4 review |
| C16 | Controlled time for musical correctness and feedback speed | C07 plus external-suite client | M5 controlled-time admission; required by Mosaic campaign |

M0: actual native runtime and generic script boot work without Mosaic installed.
M1: usable virtual device environment demonstrates a real Mosaic edit/play/save.
M2: complete software workflow suite, not just mocks, detects seeded defects.
M3: LLM iteration, independent runtime installation and official-dependency update
acceptance pass on the existing WSL profile.
M4: native Linux acceptance passes independently.
M5: controlled-time verification checks exact musical schedules alongside real-time scheduling accuracy (D18).

## C00 — Empirical foundation and scope inventory

**Depends:** P0 plus applicable user-scope amendments: completed Paranoia responses
and findings/dispositions referenced by `state.json`'s `plan_review_evidence`, with
substantive fixes resolved. Original P0 is `docs/delivery/reviews/P0-triage.md`;
the general-purpose amendment is P0A1. A pending
or errored tool call is not that artifact; no particular engine is mandatory.
**Goal:** Choose a viable runtime/host path from measured evidence before building
dependent interfaces. **Inputs:** This contract; local Mosaic inspection checkout;
upstream norns/desktop repositories and official API/protocol docs.

**Procedure:**
1. Record Windows/WSL kernel, distro/userspace, architecture, CPU/memory, filesystem
   placement, installed build/container tools and browser availability. Launch
   the pinned browser automation tool and render/control a fixture, rather than
   merely checking installation. A Windows browser runner may serve WSL. Probe the
   existing Ubuntu 20.04 environment first. Avoid unrelated package upgrades.
2. Establish the official runtime lock separately from app fixture locks as defined
   in UPSTREAM.md. Pin monome/norns and its actual official/transitive build graph,
   including libmonome/serialosc where used, with no duplicate submodule pins.
   Identify a feasible pair of official runtime refs for C14's real update test.
   Lock Mosaic/nb only in `fixtures/apps/mosaic.lock.json`. Also acquire and
   lock the README-linked `sixolet/matrix` and `sixolet/toolkit` mods and their
   required transitive dependencies for A17. Define base-MIDI and MIDI-modulation
   fixture profiles; both are mandatory at full release, while audio components
   stay out of scope. Inventory licences,
   native dependencies, build commands and Lua compatibility from source. Choose
   actual build/image versions, never `latest` as a reproducibility contract.
3. Run current Mosaic unit tests with captured inventory. Isolate their auto-fetch
   into a locked test-artifact preparation step. Run in a test environment without
   `/home/we/norns/lua/core/norns.lua`, whose presence makes Mosaic's runner skip.
   Parse luaunit totals and failures, require tests collected > 0, and reject the
   runner's skip banner even if exit status is zero. Record baseline failures honestly.
4. In disposable workspace builds, prove native runtime startup, one script-loaded
   framebuffer, key callback and grid discovery route. Also prove virtual MIDI
   port creation/enumeration in `midi.vports`, outbound note capture through
   `midi.connect(i)`, and an inbound native MIDI event callback. Probe WSL's actual
   ALSA capabilities; a container cannot supply missing host kernel facilities.
   If needed, prove a small native virtual-MIDI backend preserving norns Lua/event
   semantics rather than assuming ALSA exists. Inspect desktop projects
   only to choose a workable implementation. Identify required crone/JACK services
   and whether they can use a dummy backend. No silent assumption of audio-free boot.
5. Define the claimed generic controls/display/grid/MIDI and script-services API
   surface from official monome contracts, independently of Mosaic. Create two
   non-Mosaic probe applications with distinct code names and a sibling library.
   Prove core startup/build without app fixture caches/dependencies. Separately
   enumerate Mosaic's transitive runtime APIs, nb startup needs, mod/peripheral
   accesses, file paths and all time sources. Classify supported/absent/unsupported.
6. Convert every software feature section of the pinned Mosaic README into a
   `compatibility/workflows.json` row: feature, source, scenario IDs, oracle,
   owner card, required tier and meaningful options/boundaries. Map exclusions
   individually; whole advanced-feature sections cannot disappear as “hardware”.
7. Write `docs/architecture/runtime-decision.md` with measurements, smallest patch
   boundary, selected host/container path, build costs, and remaining unknowns.
   Amend platform thresholds now only if evidence justifies it. Preserve scope.

**Done when:** Compile/start/input/frame, bidirectional virtual MIDI and automated
browser fixture probes pass in the chosen environment; luaunit collection is
nonzero (failures, if any, are explicitly recorded rather than green);
locked source identities and baseline test results exist; every documented
software workflow has an owner/oracle; runtime/peripheral inventory is explicit.
The result distinguishes proven boundaries from deferred C02/C03 full integration.
**Outputs:** Runtime-only `dependencies.lock.json`, `fixtures/apps/mosaic.lock.json`,
generic conformance inventory, `compatibility/{apis,workflows}.json`, runtime
decision, probe sources/logs, C00 completion. **On fail:** Diagnose exact package,
transport or permission failure. Test a contained alternative before proposing a
distro change. No UI implementation past an unproven native runtime premise.
**Refs:** V01–V06, V08; ACCEPTANCE scope/oracles; RUNBOOK premise policy.

## C01 — Automation and evidence foundation

**Depends:** C00. **Goal:** Make every later feature scriptable and observable from
the outset. **Inputs:** Runtime decision, workflows inventory, proposed CLI/API.

**Procedure:**
1. Implement `dev/emu` command routing and schemas for scenarios, action acks,
   observations, capability reports, errors and run manifests. Begin with a tiny
   contract fixture; do not pretend it is a norns implementation.
   Commands take generic `--script`/`--code-root` inputs. No Mosaic-only CLI option
   or mandatory app bootstrap; fixture fetch is separate from default runtime fetch.
2. Give each session/action/run a unique identity. Define grid (1-based) vs wire
   coordinates explicitly, key/encoder IDs, monotonic timestamps, beat units,
   frame revisions, bounds and transport ordering. Reject invalid requests.
3. Implement scenario loading, assertion results, deadlines, required inventory
   checks and nonzero exit propagation. Enforce mandatory E evidence for software
   scenarios, E/R for each A01–A22 family, and platform-specific A23/A24 gates.
   Reject D-only/mock-only coverage. No `sleep`-then-unconditional-success.
   Also enforce applicable generic G01–G06 gates, independent of Mosaic results.
4. Add isolated runtime/data directories, process ownership, port discovery,
   source/config identity and explicit stop/cleanup. Bind control services locally.
5. Implement the failure bundle and evidence verifier. Test empty selection,
   missing artifacts, backend death, stale source digest and timeout rejection.

**Done when:** Contract tests prove ordering and schema errors; fixtures with a
known assertion failure, crash or missing test fail the command; successful runs
can be verified and replay recipes resolve their locked inputs. The runner clearly
labels fixture-only capability until C02 attaches the real runtime.
**Outputs:** `dev/emu`, `schemas/`, `src/automation/`, focused tests, sample manifest,
C01 completion. **On fail:** Fix runner truthfulness before attaching workflows;
never hand-edit a generated result to mark a test passed. **Refs:** A21; CLI and
artifact contract; RUNBOOK evidence rules.

## C02 — Official norns runtime, generic loading and Mosaic fixture

**Depends:** C00, C01. **Goal:** Load production norns libraries and arbitrary supported
script entrypoints, including the independently installed Mosaic fixture,
with only explicit hardware adaptations. **Inputs:** Locked sources, native
runtime spike, API inventory, launcher/protocol.

**Procedure:**
1. Turn the chosen build into reproducible scripts/container files; version any
   norns patches under `patches/norns/` with rationale and affected API contracts.
2. Start actual matron and required support services, with a separate entire dust
   root per session, not just a data directory. Mount each selected source tree as
   `<session-dust>/code/<declared-app-name>` and keep `_path.code`/`norns.state.path`
   consistent with native include/require rules and optional code-root inputs.
   Only the Mosaic fixture declares the name `mosaic`. Prove both distinct probe
   apps with all Mosaic-specific source/dependencies absent. Integrate lifecycle/logs.
3. Attach ordered input and raw screen observation at the runtime boundary. Keep
   application `include`, params, clock, metro and scheduler semantics intact.
4. In the opt-in Mosaic fixture only, load nb and its activation configuration.
   Model absent physical devices using native platform capability semantics;
   the core must not branch on application identity. For the fixture install and
   activate the pinned matrix/toolkit mods through real norns mod setup/allow-list
   for the required modulation fixture profile; verify they register expected
   parameter hooks. Keep base-MIDI startup tested without them. Audit each
   startup call; unknown APIs fail with a named capability diagnostic.
5. Load pinned Mosaic with `testing = false`; capture Lua load/init/coroutine errors
   as failures even if application code merely prints them. Use stable logging
   hooks or narrow instrumentation, not a global “any text means success” parser.
6. Implement probes for include paths, params actions, metro cancellation, clock
   coroutine errors, screen refresh and absent peripherals. Record remaining
   device dependencies to C03/C05 explicitly.

**Done when:** Generic G01/G02 boot and include contracts pass independently of
Mosaic, core has no fixture imports or app-name dispatch, and Mosaic init returns,
expected redraw and scheduler clocks are active, and a first script frame is observed without
unexpected errors. Report device attachment separately; do not invent a Mosaic
device-wait state. Failures in
init/background coroutine become structured nonzero results. No broad mocked
`_norns` or Mosaic scheduler is loaded. Repeated launcher stop leaves no processes.
**Outputs:** Build/launch config, runtime adapter, native patch notes, capability
report, C02 completion. **On fail:** Minimise failure with a probe and fix the native
boundary; never add an untracked stub to advance. **Refs:** A01/A21; V06.

## C03 — Virtual 128 grid

**Depends:** C02. **Goal:** Make Mosaic interact with a virtual grid through its
normal device callbacks. **Inputs:** Chosen grid transport and official protocol
contract, runtime, scenario runner.

**Procedure:**
1. Implement device identity/discovery, connection and teardown for the chosen
   native route. Preserve reported dimensions and 1-based Lua coordinates.
2. Implement every LED command reached by Mosaic, including bulk updates, plus
   refresh semantics and brightness 0–15. Track displayed matrix revisions.
   Cover the full grid API surface claimed by the capability manifest using
   official contract probes; Mosaic's calls are not the platform coverage limit.
3. Inject down/up events through the real grid input boundary; support multiple
   held keys, ordered chords, duplicate/invalid input policy and reconnect.
4. Test every corner and row/column boundary with an independent device probe.
   Assert raw transport and resulting runtime coordinates separately.
5. Connect actual Mosaic; verify menu button state and page changes through grid
   inputs. Add fault injection for swapped coordinates and missing key-up.

**Done when:** Grid conformance and Mosaic navigation tests pass; two held keys
remain held until their separate releases; disconnect/reset clears session input;
LED bulk/single updates agree; seeded coordinate/release defects fail tests.
**Outputs:** `src/devices/grid/`, grid contract tests, scenario fixtures and raw
matrix evidence, C03 completion. **On fail:** Inspect wire/runtime event pair;
fix adapter semantics rather than changing Mosaic's grid mapping. **Refs:** A02.

## C04 — Norns controls, rendered UI and browser automation

**Depends:** C02, C03. **Goal:** Provide faithful visual/control surfaces for users
and LLMs, with automated evidence that the browser is wired correctly.
**Inputs:** Raw runtime framebuffer, grid matrices, ordered input API.

**Procedure:**
1. Render actual 128×64, 16-level screen pixels and 16×8 LED state; preserve aspect
   ratio and nearest-neighbour scaling. Do not reconstruct Mosaic pages in JS.
2. Implement three keys/encoders, keyboard bindings, mouse wheel/delta controls,
   simultaneous grid/key holds and a visible held-state control. Route all inputs
   through the same API used by scenarios.
3. Handle pointer capture, focus loss, browser disconnect and cancellation so
   key-ups are not lost. Show readiness, errors, current script and capabilities.
4. Add browser automation using an installed, pinned browser test tool (default
   Playwright). Automate real DOM/pointer/keyboard controls and compare runtime
   event traces, rendered pixels and raw observations at settled frame revisions.
5. Exercise script pages, shift interaction, norns menu entry/exit and tooltips.
   Run the same browser control/render tests against both differently named generic
   probe apps with Mosaic dependencies absent, as required by G02/G03.
   Add a stale-frame injection that leaves backend state right but rendering wrong.

**Done when:** Browser actions and equivalent API actions yield the same normalized
runtime trace; expected controls/pages render; focus-loss/disconnect releases inputs;
wrong/stale renderer injection is caught. No human screenshot judgement is needed.
**Outputs:** `ui/`, browser tests, reference render fixtures with independent
assertions, C04 completion. **On fail:** Use DOM-to-action-to-runtime-to-frame traces
to isolate the fault; no synthetic test-only UI state. **Refs:** A02/A03/A19.

## C05 — Virtual MIDI and independent capture

**Depends:** C02. **Goal:** Exercise actual norns MIDI paths with no physical ports.
**Inputs:** MIDI API inventory, runtime device transport, runner and timestamp schema.

**Procedure:**
1. Provide deterministic virtual port identities and configuration. Attach them
   through native runtime MIDI handling (for example virtual ALSA sequencing if
   validated in C00), not direct calls to Mosaic note-generation functions.
2. Capture raw note-on/off, CC, program change, clock/transport and relevant realtime
   messages with source emission sequence and monotonic timestamps.
3. Inject input events with explicit port/channel/time; test all channel boundaries,
   velocity-zero note-on semantics, simultaneous notes, CC ranges and port selection.
4. Add a separately implemented MIDI decoder and outstanding-note tracker. Preserve
   raw bytes even when providing decoded observations. Make overflow/drop explicit.
5. Supply minimal known device configs and malformed/missing config fixtures.
   Include a virtual vport named `Norns2sinfonion`: capture the software's program
   changes at init and on scale/root changes. Physical conversion remains excluded.
   Test native input/output loopback with probe scripts and actual Mosaic selection.

**Done when:** Independent byte/channel/order round-trips pass; absent ports and
invalid config produce useful errors; capture overflow fails; timestamp source is
backend monotonic emission time; wrong channel/dropped-note injections fail checks.
**Outputs:** `src/devices/midi/`, probe scripts, config fixtures and capture tests,
C05 completion. **On fail:** Distinguish driver/port discovery from application
mapping; keep the MIDI log source independent of Mosaic's expected-output code.
**Refs:** A14; exact data and test capture gates.

## C06 — First complete Mosaic development slice

**Depends:** C03, C04, C05. **Goal:** Demonstrate the tool's value before expanding
coverage. **Inputs:** Real Mosaic runtime, browser/API, virtual grid and MIDI.

**Procedure:**
1. Seed a known MIDI device config in the session data `config/` directory before
   starting an empty isolated project. Through
   actual controls create a short four-step pattern with explicit notes/velocities,
   assign it to a channel, and start playback using the grid transport button.
2. Assert expected grid/screen state and independently specified MIDI events for
   two loops. Edit a step during playback; assert the documented next-boundary effect.
   Distinguish first boot from boot with existing autosave. Await named stable
   frames after splash/dirty refresh and include autosave in the event recipe;
   never mask the entire display to ignore animation.
3. Stop, save through the real UI dialog, restart the runtime, load through controls
   and assert that the same musical sequence returns. C11 later deepens failure cases.
4. Run the workflow once through API actions and once through automated browser
   controls, comparing normalized runtime outcomes. Package one-command replay.
5. Perform P1 on the whole slice; focus on secretly mocked paths, false readiness,
   circular oracles and device input fidelity. Fix accepted substantive findings.

**Done when:** A01 and the defined edit/play/save slice pass in fresh sessions;
browser and API reach actual Mosaic; MIDI and frame evidence is reproducible;
P1 is complete. This milestone does not claim advanced-feature coverage.
**Outputs:** `scenarios/smoke/`, expected event fixtures, M1 evidence and C06
completion. **On fail:** Reduce to shortest failed input trace and repair its
owning adapter; no UI-only milestone substitution. **Refs:** M1; P1.

## C07 — Real-time clock semantics, replay and timing

**Depends:** C06. **Goal:** Make production-clock sequencing verifiable and replayable
before broad workflow work. **Inputs:** Time-source inventory, clocks/metro native
behaviour, actual Mosaic clock/scheduler and MIDI capture.

**Procedure:**
1. Probe clock.run/sleep/sync/cancel, metro start/stop/free, tempo change, transport
   start/stop and ordering at equal deadlines. Build expected traces independently.
2. Implement real-time wait.beats, observation barriers, deadlines and action replay
   relative to transport/beat anchors. Ensure stalled coroutines cannot hang the
   harness. Exact wall-clock replay is not claimed.
3. Add an explicit repeatable random-seed hook for test sessions, covering Mosaic's
   startup reseeding without replacing native clocks/time. Record hook scope and
   compare a normal-seed smoke path. Exclude random splash-font draws from musical
   assertions by defining the input/initial-state timeline, not by sorting outputs.
4. Build emission-time measurement against an independent tempo schedule. Specify
   native pulse quantisation (including actual ppqn) and delayed note-off rounding
   as part of expected musical timing. Record unrounded intent and rounded expected
   dispatch separately so quantisation cannot hide arbitrary delay.
5. Measure capture/instrumentation overhead and run real-time contracts for
   cancellation, tempo changes, reset, overlapping notes and swing. Deterministic
   virtual time belongs solely to C16 and cannot block these real-time tests.

**Done when:** Real-time probes match independent contracts; beat-anchored recipes
reproduce expected musical content and logical order within timing bounds;
cancelled jobs do not fire; C12 can run the defined timing fixture unchanged.
**Outputs:** Clock probes, replay commands, timing report schema, C07 completion.
**On fail:** Fix real runtime contracts; do not substitute virtual-time results.
**Refs:** A07/A08; E/R tiers and central thresholds.

## C08 — Editing, channels and harmony

**Depends:** C07. **Goal:** Cover the core musical editing loop using real controls.
**Inputs:** C00 feature inventory, pinned README/pages/models, scenario DSL and
independent note/merge/quantiser fixtures.

**Procedure:**
1. Implement A04/A05/A06/A15 scenario families: trig/note/velocity editing, removal,
   channel device and port selection, assignments, masks, lengths, mute, merge,
   scales/transposition/chords and undo/redo.
2. Use small explicit patterns whose expected intersections/unions, pitches and
   velocities can be independently derived. Include empty/boundary/wrap cases and
   interactions across two channels; cover each documented merge/quantiser option.
3. Enter/edit via grid/key/encoder actions and verify before/after screen and LED
   state as well as emitted MIDI. Internal model values remain diagnostic only.
4. Run every required software scenario through E real-time runtime. C16 may later
   duplicate cases in D for faster feedback, never replace E. Link
   existing unit tests as supplementary coverage, not a substitution.
5. Seed one altered pitch/merge result to demonstrate oracle sensitivity.

**Done when:** Every owned workflow row and its enumerated scenarios passes;
independent expected tables exist; actual UI editing changes observed musical
output; wrong pitch/merge injection fails. **Outputs:** `scenarios/editing/`,
`fixtures/oracles/`, inventory coverage and C08 completion. **On fail:** Isolate
upstream vs emulator fault before changing code; follow baseline-defect policy.
**Refs:** A04/A05/A06/A15; independent oracles.

## C09 — Advanced sequencing, locks, song and modulation

**Depends:** C08. **Goal:** Verify the timing-heavy workflows most likely to escape
unit mocks. **Inputs:** Inventory, clock contracts, source/README, independent MIDI
and beat fixtures.

**Procedure:**
1. Implement A07–A11/A17 with small independently specified patterns: divisions, tempo,
   swing/shuffle, resets, probability, random note modes, trig/trigless locks,
   slides/wrap, chord articulation, song repeats/transitions and LFO modulation.
   A17 uses the pinned/activated matrix and toolkit profiles from C00/C02 to
   modulate actual Mosaic MIDI-device parameters; assert resulting emitted MIDI,
   not merely a mod's internal oscillator. Verify both documented mod paths.
2. Pin expected beat positions, pitch sets, CC/value ranges and note durations
   before observing candidate output. Test 0/100% probability and seeded intermediate
   cases without probabilistic flakes. Cover all documented option variants.
3. Exercise at least two interaction cases per family: e.g. slide across a song
   transition, tempo change during strum, muted overlapping chord notes, locks
   across channel wraps. Choose cases from source invariants, not arbitrary volume.
4. Run every required software scenario in real time. Ensure stopped/cancelled
   delayed actions cannot leak. Later controlled-time results are supplementary.
5. Add fault sensitivity for a lost note-off and wrong transition boundary.

**Done when:** Owned inventory is complete; output is checked at exact logical
boundaries; all required real-time runs pass; deliberate event-loss/transition
defects fail. **Outputs:** `scenarios/sequencing/`, expected beat/event fixtures,
C09 completion. **On fail:** Minimise seed/input recipe and inspect native timing;
do not relax timestamps until a production scheduling defect disappears.
**Refs:** A07–A11/A17; timing gates.

## C10 — Recording, controllers and MIDI device behaviour

**Depends:** C08, C05. **Goal:** Verify inbound MIDI and configuration-driven editing
through the native MIDI path. **Inputs:** Virtual ports, known device configs,
mapping/recording source, workflow inventory.

**Procedure:**
1. Implement live record arm/disarm, quantised input and lengths, held-step entry,
   chords, and controller automation recording. Replay the result to assert output.
2. Exercise norns PMAP setup and relative binary-offset controls, selected/all-channel
   mappings, input ranges, wrong port/channel and unmapped-control cases.
3. Validate device discovery/config selection, generated CC/program changes,
   Elektron sequencing options and parameter ranges. Include Sinfonion program
   changes via virtual `Norns2sinfonion` on root/scale/transport changes. Use virtual
   devices only; no physical receiver is part of acceptance.
4. Test same-note overlap, input at a step boundary, record disarm during a note,
   and controller edits while transport runs. Derive expectations from documented
   behaviour and record genuine ambiguities as explicit contracts.
5. Ensure generated output never loops back into input accidentally unless a
   scenario explicitly connects loopback. Add wrong-channel mapping injection.

**Done when:** A12–A14 scenario inventory passes with native MIDI input, recorded
playback matches the expected musical result, wrong routes do not mutate target
behaviour, and the seeded mapping defect fails. **Outputs:** `scenarios/midi/`,
config/PMAP fixtures, C10 completion. **On fail:** Examine raw port/channel bytes
before editing application mapping; isolate upstream defects transparently.
**Refs:** A12/A13/A14; exact-data contract.

## C11 — Persistence, menus and safe lifecycle

**Depends:** C06, C08. **Goal:** Make edit/reload/save cycles reliable and fully
automated. **Inputs:** Real params/PSETs/PMAPs, Mosaic project files and dialogs,
isolated data and source mounting policy.

**Procedure:**
1. Cover new/save/load/cancel/overwrite flows using real key/encoder/text dialog
   input. Implement automation access to every dialog required by these workflows.
2. Verify params, MIDI mapping, device selection, memory/undo state where documented,
   projects and autosave through cold process restart. Compare musical output,
   screen state and independently parsed essential persisted values.
3. Exercise missing directories, malformed/truncated project/config/PSET data,
   read-only destination, failed save and interrupted write at a controlled fixture
   seam. Assert existing valid user data is preserved and errors are visible.
4. Test script reload, changed-source reload, cleanup with active notes/timers and
   two isolated sessions with distinct full dust roots and source trees each
   mounted at their declared application paths (`code/mosaic` for the Mosaic
   fixture). Repeat with both generic probes to prove app/data independence.
   Never use the user's project for
   destructive/error fixtures. Separate source checkout from writable session data.
5. Verify 10 reload/reset cycles and no held input, clock/process or port leaks.

**Done when:** A03/A15/A16 owned cases pass through real menus/files; round trips
restore expected behaviour; negative fixtures fail usefully without clobber;
cleanup/reload invariants pass. **Outputs:** `scenarios/persistence/`, corruption
fixtures, lifecycle tests, C11 completion. **On fail:** Preserve the failing data
in the run bundle; fix ownership/lifecycle rather than deleting all user state.
**Refs:** Persistence contract and recovery gate.

## C12 — Full workflow, fault sensitivity and endurance gate

**Depends:** C09, C10, C11. **Goal:** Establish trustworthy complete automated
verification, including plausible failures. **Inputs:** All mandatory inventory,
runtime errors/captures, scenario families and central timing contract.

**Procedure:**
1. Reconcile each pinned README software feature section against the inventory,
   collected tests and executed assertion results. Fail omissions and blanket
   exclusions; resolve unowned features in the existing appropriate card.
   Independently reconcile every claimed generic API against native conformance
   evidence and G01–G04. Catch core imports of fixture modules and app-name
   conditionals; fixtures may contain app-specific setup, the runtime may not.
2. Run U/I/E/B families across required base-MIDI and modulation profiles and the
   10-minute R mixed-feature fixture with transport,
   concurrent editing, chords, locks and transitions. Check timestamps/phase,
   pending notes, active clocks, session/process cleanup and capture completeness.
   Schedule stopped periods around the actual 60-second autosave behaviour and
   assert its writes/completion and any actually rendered transient frames rather
   than suppressing it or requiring an unrendered splash. Every
   required software scenario has E evidence; reject D-only or fixture-only rows.
3. Complete F sensitivity checks for wrong grid mapping, lost key-up, dropped MIDI,
   wrong channel/pitch, stale screen, corrupt save, swallowed coroutine error,
   missing inventory and stale evidence. Each must fail for the intended reason.
4. Exercise panic, interrupted client, backend death, port reconnect and repeated
   start/stop without hiding stderr. Classify an environment failure separately
   from semantic failure; both block the relevant gate until corrected.
5. Perform P2 review of coverage and false-green paths. Fix substantive findings,
   then rerun affected suites. Record remaining out-of-scope limitations precisely.

**Done when:** Generic G01–G04 and every M2 inventory row (A01–A19 and A21–A22)
have passing mandatory evidence, all central timing/endurance gates pass,
each selected defect is detected by its
intended assertion, and P2 findings are closed. No manual testing item remains.
**Outputs:** M2 manifest/coverage table, F reports, P2 triage, C12 completion.
**On fail:** Block M2 with specific scenario/cause; do not disable tests, sort away
event races, increase broad image tolerances or convert required cases to xfail.
**Refs:** A18–A22 and complete acceptance contract.

## C13 — Autonomous LLM development proof

**Depends:** C12. **Goal:** Demonstrate that an LLM can actually iterate on Mosaic
with this tool instead of depending on human exploration.
**Inputs:** CLI/API, all diagnostics, clean candidate Mosaic worktree, run recipes.

**Procedure:**
1. Write `docs/development/LLM_WORKFLOW.md` with executable discovery, start,
   action/observe, minimise, edit, reload, focused-test and regression steps.
   Include complete JSON examples and failure-bundle interpretation.
2. Provide API schema/help and compact observations usable without a screenshot
   viewer; make raw frame/LED/MIDI evidence available when the LLM needs detail.
3. In disposable candidate checkouts seed two realistic source regressions: one
   control/rendering behaviour and one musical/MIDI behaviour. Save the patch and
   expected failure out of the repair agent's starting context; don't disclose the
   answer. Give it a squashed seeded snapshot with no solution/reverse-patch history
   or uncommitted seed diff revealing the edit. Avoid mere syntax errors.
4. Run an explicitly delegated fresh-context repair agent for this bounded test.
   Give the symptom, checkout, public tool/docs and expected public behaviour, not
   the patch or code location. It must reproduce, locate and fix using emulator
   evidence, add a regression, and run required checks without asking a person to
   use the interface. Preserve transcript/actions/results as evidence.
5. Independently rerun the required affected acceptance suites on its candidate;
   reject test weakening, bypassing runtime, hidden fixture edits or unrelated code
   changes. Also perform one small scripted feature-change exercise with a new
   independently specified expected MIDI result.

**Done when:** Both blinded repair exercises and feature exercise complete through
the tools with correct automated output and no manual test; independent rerun
passes and the diagnosis is supported by observed inputs/outputs. If an agent
fails, improve missing affordances/docs and rerun only the failed exercise with a
fresh context; failure is not proof of impossibility. **Outputs:** LLM guide,
example recipes, anonymised compact exercise transcripts/results, C13 completion.
**On fail:** Identify tool observability/control gap vs agent mistake; preserve
baseline and never claim usability from a scripted happy-path demonstration alone.
**Refs:** A20; V09. Delegation here is explicitly scoped to the acceptance exercise.

## C14 — WSL2 release and automatic acceptance

**Depends:** C13. **Goal:** Deliver the usable first release on the user's existing
WSL development platform. **Inputs:** Supported host decision, locked dependencies,
full mandatory inventory and LLM workflow.

**Procedure:**
1. Package `doctor/fetch/build/start/run/test/replay/stop/release-check` as a documented
   repeatable setup. Default to existing Ubuntu 20.04 WSL; if C00 justified a
   container, provide that transparently without moving the user's distro.
   Default installation must not acquire Mosaic/nb/mod sources. Separate runtime
   conformance from opt-in app fixtures; demonstrate loading an external named app.
2. Automate clean session/data bootstrap, dependency cache reuse, source checkout
   selection and Windows-browser access. Validate paths containing spaces and
   explain recommended WSL ext4 source placement if measurements require it.
3. Define a WSL automation job run from Windows into the named distro. Record WSL
   kernel/distro/container/browser facts and exercise Windows-to-WSL control path.
   A Linux CI container does not count as a WSL result. If a self-hosted runner is
   unavailable, a local one-command automated WSL release job is sufficient.
4. Run mandatory release-check on a clean supported-profile session with all
   required suites, no skipped features. Test failed install/config diagnosis and
   an upgrade/reload using retained project data fixtures.
   Implement and test UPSTREAM.md's real official-ref update, independent app pins,
   regression rejection, patch-conflict report and rollback. A no-op ref change
   or changing Mosaic simultaneously does not satisfy G05. Run full required
   Mosaic fixture after generic candidate-runtime conformance.
5. Perform P3 review on the release package. Apply substantive fixes and rerun
   affected checks; bind final manifest to final tested tree. Write release notes
   with supported source/profile identities, limits and repeatable commands.

**Done when:** G01–G06 (WSL applicability), A23 and all in-scope required suites
pass on actual WSL, the real upstream update/rollback is proven, P3 is
complete, and a new LLM can run the documented flow without manual tests. Full
Mosaic source/patch identity and data location are explicit. Native Linux remains
unclaimed until C15. **Outputs:** Setup/package scripts, WSL job, M3 release
manifest and docs, C14 completion. **On fail:** Correct supported-profile failure
or report exact missing permission/dependency; no distro switch or mock lane
substitution to label the existing profile green. **Refs:** D01/D08; A23.

## C15 — Native Linux parity

**Depends:** C14. **Goal:** Deliver the subsequent native Linux release without
forking application behaviour. **Inputs:** WSL release package and exact inventory.

**Procedure:**
1. Select and record one supported native Linux distro/architecture from the
   validated dependency stack. Use the same runtime/image, fixtures, inputs and
   source revisions; isolate host differences to launcher/device transport.
2. Add a genuine Linux CI/host execution lane and automated browser tests. Record
   host facts proving this is native Linux, not an assumed WSL equivalent.
   Run runtime-only installation with fixtures absent and generic G01–G06
   conformance, then install the Mosaic fixture for app acceptance separately.
3. Run the same mandatory full acceptance selection, with explicit platform-specific
   configuration. Compare normalized semantic outputs across platforms; timing
   passes the central contract separately on each declared profile.
4. Perform P4 only on portability changes and platform evidence. Document install,
   replay, candidate Mosaic checkout use and platform limitations.

**Done when:** A24 and unchanged cross-platform workflow inventory pass on native
Linux; semantic outputs match and timing passes independently; P4 findings closed.
**Outputs:** Linux runner/setup, M4 manifest, platform matrix and C15 completion.
**On fail:** Fix host-bound assumptions; if no native runner is accessible, record
the exact execution prerequisite and leave M4 incomplete. WSL M3 remains usable.
**Refs:** A24; V10.

## C16 — Controlled time for musical correctness

**Depends:** C07 and the generic external-suite client. **Goal:** Verify exact musical timing and speed iteration with reproducible controlled time while
preserving all existing real-time acceptance. **Inputs:** C07 time inventory and
clock contracts, working native real-time lane, independent scenario oracles. D18 authorises this card before platform releases; the Mosaic campaign requires its admitted timing capabilities.

**Procedure:**
1. Prove control of native clock/metro scheduling and relevant util/time/os.time
   and randomseed sources at a small runtime seam. Define equal-deadline ordering,
   cancellation, transport reset, timeouts and maximum work per advance operation.
2. Implement D mode and `advance` without substituting Mosaic's scheduler, note
   generators or page logic. Report mode/capability explicitly; any uncovered
   required time source makes the requested scenario unsupported in D.
3. Duplicate selected existing E scenarios in D. Compare their expected bytes,
   order, beat positions and final observable state against independent fixtures
   and real-time results. Measure speedup; do not claim exact wall-time replay.
4. Run three fresh-process repeats of every supported D scenario with identical
   seed/input timeline, including startup/autosave randomness. Results must match
   after only documented normalization. Capture every source that is virtualized.
5. Run a focused P5 Paranoia pass on clock-boundary fidelity and D-only false-green
   escape routes, within the same one-plus-one cap. After fixes, run affected E/R
   regressions and required D suite; extend release-check with a distinct M5 gate.

**Done when:** Supported D scenarios pass independent oracles and three-repeat
determinism, unchanged E/R regressions pass, P5 is complete, and documentation
states supported D scope. **Outputs:** Clock adapter, D scenarios, speed comparison,
M5 manifest and C16 completion. **On fail:** Keep the native runtime working and labelled
real-time; leave C16/M5 incomplete with a precise unsupported source/probe. Do not
claim the Mosaic timing campaign complete while required controlled-time capabilities are missing. Continue independent real-time work.
**Refs:** V07; D tier; central determinism contract.

## Completion and handoff

No card is completed in this initial plan. P0 is a plan review record, not a
runtime test. State is the resume index; generated evidence is the basis for
completion. The final delivery report links the working launcher, supported
profiles, source identity, automated coverage and remaining explicit exclusions.
It must not ask the user to finish verification on a real device.
