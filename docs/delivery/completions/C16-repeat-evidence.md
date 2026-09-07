# Reusable controlled native repeat evidence

`scripts/repeat_controlled_probe.py` runs one named generic native oracle in
three fresh processes and retains source identity, candidate identity, native
artifacts, child output and normalized observations. It fails on a failed child,
changed source/runtime, mismatched runtime identity, bad cleanup, missing
observations, input/ack mismatch or differing normalized output. Default runtime
descriptor preservation is checked separately. This does not implement M5.

Normalization retains ordered physical-style inputs, port and MIDI bytes,
logical nanoseconds, complete grid state, framebuffer digest, logical clock and
outstanding notes at every captured observation. Host timestamps, session IDs
and drawing revision counters are omitted. Three contract tests prove that
musical/visible changes remain detectable, wall-time-only changes normalize,
and runtime errors or mismatched action acknowledgements are rejected.

The final runner's three native phase repetitions passed in
`artifacts/c16/repeat-9eb7db77f5ca47a78e437d8a121c48fd/manifest.json` using the
unchanged controlled-02 installation. Full retained manifests include artifact
hashes. Reproduce with:

```sh
python3 -m unittest discover -s tests/contracts -p test_controlled_repeats.py
python3 scripts/repeat_controlled_probe.py --probe phase --install /path/to/candidate/installation.json
```

The runner also selects clock, boundaries, MIDI and tempo probes. Their existing
native assertions remain the independent oracles; selection availability does
not claim those probes have passed through this new wrapper. Fault assertions
remain in their own probes. All controlled results are still experimental;
P5 findings and the distinct M5 admission gate remain open.
