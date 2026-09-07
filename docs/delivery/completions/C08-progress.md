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
