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
