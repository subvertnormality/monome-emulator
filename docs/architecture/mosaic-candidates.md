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
