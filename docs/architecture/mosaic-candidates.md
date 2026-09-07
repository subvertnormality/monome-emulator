# Isolated Mosaic compatibility candidates

The emulator loads external applications without changing them. Compatibility
tests can expose defects in an application; a failing baseline stays failed.
Confirmed fixes are prepared separately and do not modify the user's Mosaic
checkout or the pinned baseline fixture.

Current opt-in candidate: `memory-preserve-pattern`, based on Mosaic
`160d1ea7506773e65f298094e11d005dcb568dff`. The exact patch and supplementary
regressions are hashed in `fixtures/apps/mosaic-patches/manifest.json`.
Partial note-mask history operations must preserve unspecified working-pattern
trig, velocity, length and note-mask fields. The baseline temporarily clears a
trig during redo and loses the first-cycle note; the candidate fixes that behavior.

```sh
python3 tests/mosaic_candidate.py
python3 tests/mosaic_memory.py --candidate
python3 tests/mosaic_candidate_units.py
python3 tests/mosaic_candidate_regressions.py
```

The preparation command prints an owned code root under `.runtime/candidates/`.
It checks the baseline revision and tracked cleanliness, verifies patch/test
hashes, copies the application and records the resulting content identity.
An existing changed or incomplete candidate is rejected and preserved for
inspection. The normal emulator can load this root using its existing `--script`
and `--code-root` options; no Mosaic-specific runtime implementation is involved.

Candidate workflow artifacts include candidate.json and the actual loaded
application hash. Registered candidate packages explicitly select the candidate
when replayed. They cannot pass with missing patch identity, a different declared
patch set or an unpatched/different loaded application. Diagnostic baseline cases
remain available separately. Release manifests must state the exact supported
application revision and patch set; a candidate does not silently become the
default fixture or an upstream change.

A second opt-in candidate, `midi-counts-and-mask-clearing`, is declared in
`fixtures/apps/mosaic-patches/midi-counts.json`. It balances repeated-pitch
note-ons with their corresponding note-offs and makes the documented shift-K2
clear-all action remove channel-wide mask defaults. Run its native package with
`python3 tests/mosaic_global_masks.py --candidate`; omitting the option runs the
unpatched failing baseline. `tests/mosaic_mask_candidate_units.py` compares the
existing unit suite plus a clearing regression, and
`tests/mosaic_midi_candidate_regressions.py` checks unchanged chord behavior.
The complete release patch set must be combined and revalidated at C12.

Patch application runs outside enclosing-repository discovery, verifies content
changed, and checks reverse applicability before recording a new candidate.
This prevents Git silently skipping git-format paths in nested owned copies.

The opt-in `tresillo-repeat-bank-bits` candidate in
`fixtures/apps/mosaic-patches/tresillo.json` repairs nil bit reads when a tresillo
segment exceeds a16-bit drum bank. It repeats the source pattern at its actual
bit length. This is an explicit candidate interpretation of repeating rhythms;
it preserves all previously defined reads, without padding missing bits or
changing the upstream fixture. `python3 tests/mosaic_tresillo.py --candidate`
runs the previously failing64-step physical-input recipe and independent hit
positions. It still needs combined release-patch validation at C12.

The `pattern-length-cutoff` candidate in
`fixtures/apps/mosaic-patches/pattern-lengths.json` makes a source pattern's
note duration stop at its next trig, matching the documented rule and grid
length display. Effective lengths are computed without changing stored edits,
then supplied to existing merge modes; explicit channel/step length masks still
override the merged result. `python3 tests/mosaic_pattern_lengths.py --candidate`
runs the failing collision and unchanged duration-control packages. Wrap,
merge/mask interactions and the combined patch set remain release obligations.
