# C08 — Work in progress

C07 dependency passed and was published at `d11c8f9`. C08 is not complete.
There are 34 required software sections owned by C08 in workflows.json.

First actual-runtime package passed: `A04-pattern-editor`, seven checks,
`artifacts/c08/4300994495e040dd96603290744c9c06/manifest.json`.
It creates a four-step pattern, removes/restores a trig, changes E4 to G4,
changes one velocity from 117 to 97, cycles editor pages and checks retained
behaviour. Literal native MIDI and exact LED checks accompany the controls.
The independent pitch comparator rejects a deliberately altered output pitch.
This is an implementation checkpoint, not completion of algorithms, all editing
options or the broader A04 family. Final C08 collection must use the final source.

`tests/mosaic_workflows.py` provides a fixture-only driver for subsequent packages;
the runtime never imports it. `tests/mosaic_merging.py` authors A={1,2}, B={2,3}
through physical-style controls. Set-membership expectations are Skip={1,3},
Only={2}, All={1,2,3}; the shared E4 velocity is (117+97)/2=107. Distinct pitches
at the non-overlapping steps expose an incorrectly selected merge. It also
requires silence with no assigned patterns.

Oracle questions to resolve with real regressions before adopting expectations:

- README Lower note/velocity prose says average minus minimum, whereas the
  pinned pattern.lua computes `2*minimum-average`. Length prose differs again.
  Preserve this discrepancy in a minimal case; do not choose only values where
  the formulas happen to coincide and claim boundary coverage. Compare the
  existing literal unit contracts, documented musical intention and actual MIDI;
  apply ACCEPTANCE.md's baseline treatment for a confirmed upstream defect.
- README velocity page prose approximates endpoints (127–67 / 58–0); its fourteen
  native fader entries interpolate and floor across the full 0–127 MIDI domain.
  Boundary cases need explicit integers and a cited rule, not captured goldens.

Useful control coordinates established from the pinned handlers:

- Global channel/pattern navigation: (3,8)/(5,8). Pattern pages cycle trig,
  note, velocity. Pattern selector is row 1; channel assignments are row 2.
- Trigger grid is rows 4–7. Channel length uses held start then end. Note/velocity
  groups of sixteen steps use (9..12,8); note pitch-range controls (14..16,8).
- Channel merge buttons: trig (14,8), note (15,8), velocity (16,8), shifted
  (16,8) for lengths. Holding a merge button and tapping row 2 selects a source
  pattern, including unassigned patterns.
- Channel Norns pages: Masks 1, Trig Locks 2, Memory 3, Clocks 4, Device Config 5,
  Note Dashboard 6. Memory K2 undoes all; K3 reapplies all; shifted forms clear
  history after applying the operation. E3 traverses individual history events.

These are implementation inputs, not substitutes for output acceptance. No
Mosaic application globals may be mutated by the driver.

Trigger merge package passed seven checks in
`artifacts/c08/79c5be94b6904a1888297843ca0f0076/manifest.json`.
The documented Lower velocity baseline failed as intended by its literal formula:
`artifacts/c08/f329fc6d6b0f45ee86914ddbb496465b/manifest.json` records actual 87
versus documented 10 for overlapping 117/97 velocities. An asynchronous user
question asks which intended behavior should govern compatibility. That decision
blocks the conflicting value-merge oracles, not independent C08 work. No required
case may be waived, marked xfail or accepted from this diagnostic failure.

Memory baseline failed in
`artifacts/c08/a8a88d024bff4db19db38ae80f8dbe1f/manifest.json`: redo of a note-only
mask clears the underlying pattern trig, losing the first-cycle note before the
next pattern rebuild. memory.lua supplies zero/default values for missing event
fields. An explicit isolated candidate preserves existing working-pattern fields;
it has its own patch/test manifest under fixtures/apps/mosaic-patches and an owned
copy prepared by tests/mosaic_candidate.py. Baseline/user checkouts are untouched.
The candidate passed all nine memory controls in
`artifacts/c08/45c5d1e5820f48ec801bf669e47e9f44/manifest.json`, with an explicit
hashed candidate.json. Earlier development pass: `e29bd4e8be134608b3bedfd7d2d4c8c2`.
The registered primary memory package replays with `--candidate`; the unpatched
diagnostic uses a separate baseline ID. The verifier requires the declared patch
set, base revision, patch manifest hash and matching loaded application digest.
Three altered-evidence cases reject absent provenance, wrong patch identity and
wrong application identity in
`artifacts/c08-evidence-faults/151a5f50406848d3b0cb19532296a19b/fault-results.json`.

The isolated unit comparison is
`artifacts/c08-unit/62d9e0b5fcba4c4db61cf6b88195b759/results.json`: baseline 476
collected, 474 successes, two new regression failures; candidate 476/476 passing.
Both copies use the locked local norns Lua libraries and avoid downloads.
The existing real editing/merge workflow also passed seven checks on the candidate:
`artifacts/c08/2efe44d5d03a416b82e94217220d8aff/manifest.json`.
This is a validated opt-in candidate, not a change to the default fixture or an
upstream publication. C12/C14 must transparently select and record the full supported
Mosaic revision plus patch set, including any additional confirmed defects.

K1 shift gestures also now wait beyond
official menu.lua's 250 ms script-key hold threshold; a short tap opens the menu.

## Subsequent real-runtime coverage

All cases below use unmodified pinned Mosaic, fresh sessions, actual key/grid/
encoder inputs, exact MIDI comparisons, retained input traces and cleanup checks.
These are development evidence; the final C08 suite must bind the final tree.

| Package | Checks | Manifest under artifacts/c08 |
|---|---:|---|
| A05-channel-routing | 6 | 3397401b233245e587e70cdbc00a4211/manifest.json |
| A05-muting-channels | 7 | 8db8b4bc54be4640913edcf7d9f9448d/manifest.json |
| A06-harmony-design | 11 | b37d1eee4055433fb37578517f49d21d/manifest.json |
| A05-channel-range-boundaries | 7 | 64eace8ce8d84cd5b4a3674b6f6925e2/manifest.json |
| A06-mask-removal-controls | 8 | 6fee53ee515d4c468f417a2a1c3f0191/manifest.json |
| A06-adding-chords | 10 | 4067dae184e3460ebfc8be55a0832146/manifest.json |

Routing covers MIDI channel/port selection, cancellation and restoration. The
first driver incorrectly assumed cancellation retained field focus; failed run
`a2d7693dbc8243488c67c77cbe52c10e` led to explicit navigation from the native
device selector. Muting covers both documented gestures and channel isolation.

Harmony uses literal pitch tables in fixtures/oracles/harmony.json for major,
minor, root E, degree II, rotation, +/-12 semitone limits and cancel/restore.
The independent framebuffer header renderer accepts the scale page's three-tab
layout. This does not close every scale editor/quantiser option.

Channel ranges cover offset two-step and three-step loops, another channel's
independent range across a row boundary, 64 steps and restoration. The 64-step
case emits four notes then sixty silent steps: expected gap 10.166666667 seconds,
actual 10.167554873, with a fixed 50 ms bound on native emission timestamps.
The driver permits an explicit longer observation deadline for this real-time
loop. The documented independent one-step gesture remains unresolved: the pinned
dual-press handler consumes two distinct held keys; short/long channel handlers
do not set a one-step range. The separate global length fader can clamp to one
but does not prove independent channel selection. Full Channel Length stays open.

Mask controls verify trig suppression/restoration, independent note overrides,
single-step removal, whole-channel clearing and repeated empty-step clearing.
Chords verify one through four additional voices, fourth-voice +/-14 diatonic
degree bounds (MIDI36/84 from C60), clamp behavior and removal. Articulation
modifiers remain C09 obligations; MIDI-keyboard mask entry remains C10.

Commands: `python3 tests/mosaic_channels.py`, the same with `--mute`, and
`python3 tests/mosaic_harmony.py`, `tests/mosaic_lengths.py`,
`tests/mosaic_masks.py`, `tests/mosaic_chords.py`, run sequentially in WSL.

## Channel defaults and isolated MIDI/mask candidate

`tests/mosaic_global_masks.py` applies a channel-wide velocity80, a step override110,
a channel-wide G3 note55, a step overrideA4 note69, channel trig-off and a step
trig-on override. The final shift-K2 must remove all masks and restore the pattern.

The unpatched baseline fails counted-note drain in
`artifacts/c08/a9eb66b7e7ef48d3a3b41e86691dd2c1/manifest.json`: eight note-ons for
pitch55, one note-off, outstanding count7. m_midi.lua emitted every note-on but
collapsed note-offs until its internal count reached zero. This reproduces R08.
The isolated 0002 patch emits every corresponding note-off and keeps bookkeeping.
No emulator capture or expected-event rule was weakened.

Candidate preparation first rejected a malformed hunk; after correcting it,
`11bb43c7abee4cfd8b0a63e35e56afe0` still failed. Inspection proved Git had silently
skipped the git-format patch in a copied directory below the emulator repository.
Preparation now sets a repository-discovery ceiling for patch application,
requires a changed application digest and verifies reverse applicability. The
earlier memory patch used plain unified diff and its recorded candidate actually
contains the verified memory change. Failed/incomplete copies remain preserved.

With the MIDI patch actually applied, `662d17b2bd704bd28733400bf09e87b1` passed
the first six mask checks, then failed clearing: program.clear_masks_for_channel
removed step masks but retained channel defaults, including trig-off. The README
instructs shift-K2 to remove all masks on the channel. The 0003 isolated patch
clears all eight global mask defaults as well as existing step masks. The sole
production caller is the channel's shift-K2 mask action.

The explicit `midi-counts-and-mask-clearing` candidate is declared in
`fixtures/apps/mosaic-patches/midi-counts.json`. All eight native checks pass in
`artifacts/c08/fe3d8da9d6a34327998b23b6f43571c2/manifest.json`.
The unchanged four-voice chord package passes ten checks in
`artifacts/c08/a214ed9f0d2c4dc8870e546b96ef9721/manifest.json`.
The supplementary comparison in
`artifacts/c08-mask-unit/77a4cc5bf7fb44a384c7009498fa14d7/results.json` collects475:
baseline474 successes/one new regression failure; candidate475 successes/zero
failures. It checks clearing all eight defaults while preserving another channel
and underlying pattern data. An initial reporting parser failed on LuaUnit's
singular "1 failure"; both singular/plural forms are now parsed.

Reproduction: `python3 tests/mosaic_global_masks.py` retains the failing baseline;
add `--candidate` for the explicit candidate. Run
`python3 tests/mosaic_mask_candidate_units.py` and
`python3 tests/mosaic_midi_candidate_regressions.py` for supplemental regressions.
The unit runner was first executed from an identical ignored development copy;
the final committed runner includes the corrected singular/plural parser.

This candidate remains separate from the memory candidate and the default Mosaic
fixture. C12 must assemble and verify the complete release patch set, including
overlap/panic/stop and combined-memory regressions. These C08 results do not close
all R08/A18/A22 obligations or claim a complete Mosaic release.

## Scale slots, complete scale choices and rhythm controls

| Package | Checks | Manifest under artifacts/c08 |
|---|---:|---|
| A06-scale-slot-controls | 13 | b68a36fc5c2c48c9ae76021db1a88ee4/manifest.json |
| A04-euclidean-paint-controls | 8 | b2e8d41ce9ca47a39a2a4fd0f2a05543/manifest.json |
| A04-rhythm-bank-controls | 11 | a64ab28e58334f508c1f96dde84eaa82/manifest.json |
| A06-ten-scale-choices | 13 | 996ec9dc738544fcbb08fd1a34629eaf/manifest.json |

Scale slots cover first/last selection, shift/long edit without applying,
retention, global semitone increments/decrements, center, endpoints and addition
to a per-scale transpose. The separate scale-choice package plays all seven
degrees of all ten scales against independent interval tables in scales.json,
including upper/lower selector clamps. Full quantiser-option/scale-lock coverage
remains outstanding.

The initial scale-slot run `7af59ee065a04cd9a23e1404d477c631` exposed R15:
after stop, the active-slot highlight disappears while edit-only LED4 is correct.
The scale-controls package tests the edit-only indicator and MIDI behavior;
the stopped active highlight is a separate mandatory C12/A19 obligation. Its
minimal executable diagnostic is `tests/mosaic_scale_slots.py --highlight-baseline`:
`artifacts/c08/87f94249f664467bbd473ed4e16986f6/manifest.json` fails the expected
slot1 LED15 assertion with actual2. No highlight acceptance was waived.

Euclidean controls use the independent 3-in-8 table {1,4,7}, shifted {2,5,8},
and XOR with entered steps {1,2,3,4}. Preview leaves MIDI unchanged; cancel,
shift, left/center reset, repaint undo and a dense fill are verified. The bank
package decodes selected immutable rhythm data into literal step sets; it never
calls Mosaic's algorithm to generate expectations. All five drum banks and
all four numeric masks are exercised, including empty output and full 64-cell
repeated patterns. Tresillo variants and remaining fader boundaries remain open.

Reproduce with `python3 tests/mosaic_scale_slots.py`, `tests/mosaic_euclidean.py`,
`tests/mosaic_rhythm_banks.py`, and `tests/mosaic_scales.py`, sequentially in WSL.
These results are development checkpoints; no C08 completion is claimed.

Two active channels pass eight checks in
`artifacts/c08/61cf260f8f034f86880c5f51adaa13e6/manifest.json`:
the same pattern feeds MIDI channels1/2, channel2 is one octave higher and loops
three steps while channel1 loops four, then two. Muting/unassigning channel2
preserves channel1; restoring assignments and lengths restores both streams.
The first driver assumed ascending simultaneous channel order and failed in
`ec85f61160a44f6eb7fd0059e10d7c65`. Pinned m_clock.lua:328 constructs channel
clocks from17 down to1; the corrected expectation retains that exact order.
Captured MIDI is never sorted or otherwise reordered to make the comparison pass.

A second asynchronous clarification asks how the user currently selects an
independent one-step channel, given the two-distinct-key gesture in the pinned
source. The Lower merge semantic question also remains pending. Neither question
blocks the independent root/degree/rotation and editor-option packages.

All harmony selector axes passed through seven-note musical tables:

| Package | Checks | Manifest under artifacts/c08 |
|---|---:|---|
| A06-twelve-scale-roots | 15 | fdd2628a8af74bb38583180f9631f8c4/manifest.json |
| A06-seven-scale-degrees | 10 | 373cdcdbedc54cc98a8b90eca27a780b/manifest.json |
| A06-seven-scale-rotations | 10 | 893bf97056084a7d84ccd3a48fb9f0b7/manifest.json |

Each axis includes its upper/lower selector clamps. Degree expectations advance
through a diatonic interval table with octave carry; rotation lowers the highest
N positions in a seven-note voicing by an octave. These independently specified
pitch rules do not call Mosaic's quantiser. Commands are
`python3 tests/mosaic_harmony_axes.py`, with `--degrees` and `--rotations` for
the other two packages. They supplement, rather than complete, quantiser-option
and scale-lock interaction coverage.

Editor range and group packages also passed:

| Package | Checks | Manifest under artifacts/c08 |
|---|---:|---|
| A04-note-range-controls | 11 | f2aa8a8c38db4874a01a7aac8989fd41/manifest.json |
| A04-velocity-range-controls | 21 | c4331bd66b4d4f3e8bd72370505f6823/manifest.json |
| A04-four-step-groups | 7 | d1aa372f9bd54a57b67a7a66712714b2/manifest.json |

`tests/mosaic_editor_ranges.py` tests successive single-step range moves, both
long-press extremes, clamps and center restoration. `--velocity` covers all14
uniformly spaced velocity entries using floor(127*(14-index)/13), range movement
and zero-velocity silence. This yields68 at the seventh entry; the README's
first-page summary says67, an inaccurate bound rather than the implemented
14-point quantisation rule. The literal table is not captured from test output.
`--groups` shift-copies note and velocity edits, verifies all four visible groups,
then plays ranges1–4,17–20,33–36 and49–52 to prove the edits reached each group.

## Tresillo boundaries and bounded fixture observations

All eight tresillo multipliers (8 through 64) passed ten checks in
`artifacts/c08/f2889239f6294349bc12635d0002a5a6/manifest.json`.
The expected hit positions are hand-derived from two 3m segments of pattern A
and one 2m segment of pattern B; exact LEDs, pitches and velocities are checked.

The drum-bank boundary baseline failed in
`artifacts/c08/22731dae6de5485d95a6ff25a870664a/manifest.json`.
Its retained matron.log reports `Coroutine error:` at drum_ops.lua:22 because
bit32.band received nil. Banks2–5 contain 16-bit patterns, while the larger
multipliers request up to24 bits. The scheduler catches and prints this failure,
so the initial driver surfaced a missing-LED timeout. This is an unresolved
Mosaic candidate-fix obligation within C08, not an excluded workflow.

The successful multiplier package retained 924,907,777 bytes of observations
against 1,315,814 bytes of native events. Repeated wait polls copied full MIDI
history and framebuffer, causing minutes of redundant evidence verification.
The C08 fixture driver now retains the first and final observation of each
separate wait and records poll counts. Every poll still evaluates its predicate;
all native inputs and MIDI remain unabridged. Distinct waits retain distinct
witnesses. The shared C05/C07 driver and runtime clock are unchanged.

The fixture also checks incremental matron output for Mosaic's caught scheduler
errors, including after cleanup. Four focused tests pass for separate witnesses,
timeouts, propagated predicate errors and fragmented scheduler diagnostics:
`python3 -m unittest discover -s tests -p test_workflow_retention.py -v`.
The full native multiplier rerun and boundary diagnostic are pending in session
54985, logs `artifacts/c08-tresillo-retention.log` and
`artifacts/c08-tresillo-diagnostic.log`. No C08 completion is claimed.

The retention rerun passed all ten checks:
`artifacts/c08/89a695ac0c27491f9713f4e67fcba9af/manifest.json`.
Its observations total32,945,962 bytes, a96.4% reduction from the preceding
924,907,777-byte bundle. The exact same rhythm/pitch/velocity assertions pass.
The boundary diagnostic now fails explicitly with `mosaic_coroutine_error` in
`artifacts/c08/fef9e7ab31fd435ab874c79f8029a0eb/manifest.json`, preserving the
Mosaic source location and nil-bit argument instead of reporting only a timeout.

An isolated candidate wraps rhythm-bit reads at each bank pattern's actual
stored bit length. This extends the existing repeating-pattern interpretation
into tresillo's larger segments, retaining every previously in-range bit.
For bank2 pattern2 (hits1/9 in16 bits), the64-step 24/24/16 segmentation should
emit hits1/9/17/25/33/41/49/57. That literal expectation existed in the failing
baseline before the candidate was implemented. The candidate does not change
Mosaic's pinned fixture or the user's checkout. Its native validation is pending.

Global quantiser menu options passed through actual keys/encoders and MIDI:

| Package | Checks | Manifest under artifacts/c08 |
|---|---:|---|
| A06-all-pentatonic-option | 5 | 6c561058344a4cf988b87ae056a99da3/manifest.json |
| A06-mask-quantiser-options | 9 | 7c5f4ba568f84aceb93a962a50b3b4fd/manifest.json |

The pentatonic test uses C/D/F/B and independently expects C/D/E/C after snapping
to C-major pentatonic, then restoration on disabling the option. Mask tests
exercise default snapping, raw chromatic notes with snapping off, degree and
rotation immunity for snapped masks, full quantisation overriding snap-off,
full degree/rotation changes and restoring both switches. Page header assertions
verify return to the script after the native parameter menu. Commands are
`python3 tests/mosaic_quantiser_options.py` and the same with `--masks`.
Per-step full-mask override, random/merged pentatonic options and scale locks
remain outstanding; these two packages do not complete the quantiser inventory.

The isolated tresillo candidate passed its exact64-step LED, note, velocity,
repaint and cleanup assertions in
`artifacts/c08/25ffba5f465e4a0b9b18cbc87837ac05/manifest.json` (two registered
checks). No scheduler error occurred. This closes the reproduced bank2 boundary
for this candidate; other banks/multipliers and combined patch regressions remain
required before the full release. Session98079 exited0 after both quantiser
packages and the candidate completed.

The next slot-selection package initially failed in
`artifacts/c08/d47de10132254412a266ff2b817da294/manifest.json` because the test
expected an unassigned button to be dark. Pinned controls/button.lua specifies
off=2 and on=15. The driver was corrected to that explicit rendering contract;
no runtime or Mosaic behavior changed. The hold-selection edit was also made
nonvacuous (C to G) before rerunning. Active session18739 is running
`tests/mosaic_pattern_slots.py`, log `artifacts/c08-pattern-slots-corrected.log`.

All23 pattern-slot checks passed in
`artifacts/c08/9d0bbb8425784ce7ab1389df9319ad91/manifest.json`.
Every slot is edited and independently assigned through the native grid path.
Returning to slot1 preserves its original four-note pattern. Note and velocity
editors both pass shift-selection and long-selection with nonvacuous MIDI edits.
The source-contract correction above is retained alongside the successful run.

Active session60913 now runs `tests/mosaic_pattern_lengths.py`, then its
`--collision-baseline` case. Logs are `artifacts/c08-pattern-lengths.log` and
`artifacts/c08-pattern-length-collision.log`. These compare visible length LEDs
and actual MIDI note-off timestamps against one/three-step durations at90 BPM,
long-press reset, empty-step rejection and the documented next-trig cutoff.

The five ordinary length-control checks passed:
`artifacts/c08/2b35d14dd2994307b30380914de1ae1d/manifest.json`.
The maximum absolute measured duration error was2.952 ms against the existing
10 ms focused bound. The documented next-trig cutoff baseline failed in
`artifacts/c08/b5dd3ad8de1a4edbb5b45bb4378b2433/manifest.json`: the grid ends
C at the next trig, but C's MIDI duration is0.664371 seconds instead of the
expected2/6=0.333333 seconds. Other note durations differ by less than0.4 ms.
This is semantic duration disagreement, not scheduler jitter.

An isolated `pattern-length-cutoff` candidate computes each source pattern's
lengths up to its next trig before merging. Stored editor lengths remain intact,
and subsequent channel/step length masks keep their explicit precedence.
Native collision and unchanged length-control regressions are active in
session72673, log `artifacts/c08-pattern-length-candidate.log`. Combined patch,
wrap, merge and mask interactions remain obligations before release.

The isolated length candidate passed the collision package (two checks) in
`artifacts/c08/608ad456e4be471888cc611c1cc4c41f/manifest.json` and the unchanged
length-control package (five checks) in
`artifacts/c08/e569af26224c47909cd8fe4cce1397b5/manifest.json`.
The unchanged474-test upstream suite also passes on both baseline and candidate:
`artifacts/c08-patch-unit/5b65014afc3841a49e8343fd3ce8b8d1/results.json`.
Reproduce with `python3 tests/mosaic_patch_units.py fixtures/apps/mosaic-patches/pattern-lengths.json`.
These unit tests remain supplementary to the actual-input duration evidence.

The playback helper now rejects an empty note expectation or nonpositive/noninteger
cycle count before any input. Silence must use an explicit timed assertion;
it cannot earn a pass from waiting for zero events. All five focused fixture
retention/error/empty-playback contracts pass. This is a guard against future
vacuous tests; existing intentional silence workflows already use timed waits.

The tresillo candidate also passes all474 unchanged upstream tests on both
baseline and candidate:
`artifacts/c08-patch-unit/47036efed0274bf0a472fa0eb49cd93c/results.json`.
Reproduce with `python3 tests/mosaic_patch_units.py fixtures/apps/mosaic-patches/tresillo.json`.
The shell wrapper combining the two runs exited1 because its status-variable
expression was malformed across the Windows/WSL shell boundary. Each underlying
Lua test subprocess recorded exit0. `python3 artifacts/verify_patch_unit_results.py`
then exited0 after checking both result sets, exact474 counts and retained log
SHA256 values. No failed test was converted into a passing result.

This checkpoint remains C08 development evidence. Full pattern wrap, remaining
merge/quantiser/mask variants, Note Dashboard assertions and the final owned
inventory reconciliation/package run remain. The known Lower formula and
independent one-step-channel questions remain pending. Combined candidate patches
and their interactions still require C12 acceptance; no manual/hardware gate is
introduced and the default Mosaic fixture remains the pinned unmodified source.
