# C16: actual Mosaic modulation output

Mosaic behaviour branch9d7e3a4 adds two native-menu workflows, with independent
framebuffer label/value assertions and exact emitted MIDI expectations:

- M-MOD-001 routes toolkit macro1 through Matrix to Fixed Note, verifies the
  affected pitches, clears the route and requires original pitches to return.
- M-MOD-002 configures a4-beat50%-width pulse LFO and verifies two complete
  modulation periods plus every steady-state note onset against90BPM. The
  opening-pulse issue remains separately exposed by M-LEN-001.

The original pinned matrix fails M-MOD-001 in both real and controlled time.
Its menu correctly shows no depth but its parameter still holds stale modulation,
leaving every note at127. A two-line isolated dependency candidate clears that
cache and re-applies the non-trigger parameter. The unchanged case then passes
both modes; the LFO regression also passes. Original mod checkouts and Mosaic
production code remain unchanged. --mod-patches explicitly selects a per-run
copy with before/after/patch SHA verification and records it in the case manifest.
The unpatched baseline is never silently xfailed or admitted as a release pass.

Real-time LFO steady onset error is at most0.551ms in this run. Three fresh
controlled LFO cases match exactly in physical input recipes, logical MIDI,
grid, framebuffer and final clock/note state, and satisfy the2ns timing bound.
This is not10-minute endurance proof or coverage of all modulation domains.

Mosaic docs/testing/state.json and bugs.json carry portable evidence paths and
SHA digests. Key run IDs in its sibling mosaic-behaviour-runs directory:

- Failing original matrix:87d8fe350096421b8be14a068ec90f34 (controlled),
  66dfb654ea454650ab5a932ee2e71293 (real time).
- Passing clear-depth candidate:27927a98cceb44779a632fc45c4b630f (controlled),
  fc595e4fdff54f55ae3368a17b760e9c (real time).
- Passing LFO timing:bf224097012c4732bc65d51db82f6fd9 (real time),
  repeat-98e437c855144a2c8321d40714a0db56 (three controlled repetitions).

Next: reproduce the separate held-source binding suspicion in matrix, continue
the Mosaic opening-phase investigation, implement the M5 gate and perform Codex
P5. No emulator dependency/default installation change was needed for these
workflows. Controlled admission and the full manual/release campaign remain open.
