# Controlled-time admission gate implementation (not admission)

`release-check --milestone M5` now consumes one complete evidence index rather
than an unconditional unsupported response. The index must pass independently
verified native repeats, real-time regressions, expected-fault checks, external
application comparisons and a source-bound resolved Codex P5 receipt. It does
not promote the candidate runtime or certify the remaining release milestones.

`compatibility/controlled-admission.json` requires eight controlled probes and
seven native check packages. Its separate opt-in application contract requires
ten case/profile comparisons, including the currently failing M-LEN-001. The
emulator runtime imports no Mosaic code. This selection establishes C16's
comparison scope; it does not replace the exhaustive manual inventory.

Collect native checks with `python3 scripts/collect_clock_check.py --check NAME
--install CANDIDATE_INSTALLATION`. The check names are in the contract. Collect
controlled repetitions using `scripts/repeat_controlled_probe.py`. Assemble the
index with `scripts/assemble_clock_admission.py --candidate PATH --build-inputs
PATH --external-index PATH --review PATH --output PATH`, adding one `--repeat`
per probe and one `--check` per native package. The external index maps application
name to `profile/case` entries, each containing `real_time` and `controlled`
references (`path`, `sha256`). Controlled references identify external three-run
packages. Missing evidence fails; assembly retains the rejected index for diagnosis.

External comparisons verify each child artifact inventory, native source/runtime
identity, current application identity, clock mode, service cleanup, distinct
sessions, input order and acknowledgements. Observed MIDI bytes and timestamps
must match the raw native emission prefix, and frame revision/hash pairs must
exist in the native trace. Unexpected native errors fail. Three controlled runs
must match; ordered final MIDI, grid and screen outputs must match real time.
The executable application cases retain responsibility for musical expectations.

Focused evidence collected during implementation:

- `artifacts/c16/check-21a4a83ce1ec4a64aff25f760e3e4144/manifest.json`:
  candidate real-time source transition passed.
- `artifacts/c16/check-73b9d03732c0472c987a263a3696e479/manifest.json`:
  candidate real-time clock suite passed all three tests.
- `artifacts/c16/check-057be805826248c6a0edde92f2cc7fda/manifest.json`:
  both controlled source-fault cases passed.
- Five admission contracts pass, including altered-output rejection in both
  clock modes. Native observation binding additionally passes against retained
  Mosaic M-MOD-002 real-time run `08bbd0b9072c41f9ae0a959026af2da1` and the three
  children of `repeat-0d3e9748636549a59bcfde6f6cf99b30`.
- Broad discovery ran 46 tests successfully and failed to import `test_clients`
  because the invocation omitted `PYTHONPATH=src`. Rerunning that one module with
  the required source path collected and passed its remaining test. Existing
  subprocess ResourceWarnings remain a C11 lifecycle obligation; they are not
  suppressed or represented as resolved by this gate change.

These are focused development checks. Earlier native packages predate the final
verifier edits and are not fresh-source M5 evidence. M5 remains not run, P5 remains
open, and controlled-03 remains explicitly experimental. Next resolve Mosaic's
opening phase, exercise the full external comparison verifier, collect the final
required evidence, and use the remaining focused Codex follow-up.

The selected application contract now also requires M-TIM-001 (twenty phrases)
and M-TIM-002 (five restart phases), bringing its required case/profile pairs to
twelve. These exercise the opening-phase correction directly. Neither may be
omitted from the final real-time/three-controlled-repeat comparison inventory.
