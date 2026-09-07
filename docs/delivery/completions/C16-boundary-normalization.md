# Expected runaway failure in controlled repeats

The first current-lock batch passed all seven non-queue generic clock groups
and three clock repeats. Boundary repeat
`repeat-e40c8df7c79d4b8086be814cdebb8d80` then stopped with `KeyError: ack`.
Its native child `0497341a2e9445f08339586ad4ed6a96` passed: the deliberately
runaway advance returned the required work-limit error. The repeat normalizer
incorrectly assumed every recorded input had a success acknowledgement.

The normalizer now permits only the boundary probe's final zero-time advance
with the exact public Lua error, matching native diagnostic, native advance
input and declared child expected fault. The normalized result retains that
failure separately; unrelated errors are rejected. No runtime or Mosaic
production code changed and no timing threshold changed.

Eight focused contracts pass across `test_controlled_repeats.py` and
`test_controlled_evidence.py`, including altered error codes, diagnostics,
probe identity, advance values and duplicate native errors. Three fresh native
boundary runs pass in `artifacts/c16/repeat-c03ee342598641bc9ce293621fb8b09c/manifest.json`.
The original failed evidence remains retained. This verifier source change
requires fresh M5 evidence for the remaining generic, queue and application
comparisons; earlier passes are historical. P5 and full delivery remain open.
