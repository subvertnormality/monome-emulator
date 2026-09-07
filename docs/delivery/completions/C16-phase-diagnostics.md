# C16: native sync phase and Mosaic diagnostics

Controlled time remains experimental; P5 and M5 are not complete.

`tests/controlled_phase_native.py` drives an independent generic script through
native keys and clock advances. At120BPM, two immediate Note Ons at1ms and504ms
followed by48 native96PPQN syncs must end at250000001ns and750000001ns. The oracle
comes from absolute beat boundaries and the native strict comparison, not captured
Mosaic output. Full-native run `artifacts/c16/b7c813e19b8742bfa169161a0bd26dce`
passes all exact timestamps and note drain checks. The candidate is selected via
the ignored `artifacts/c16/current-candidate.json` locator; the default installation
and runtime lock remain unchanged.

Reproduce with:

```sh
python3 tests/controlled_phase_native.py --install /path/to/candidate/installation.json
```

The separately owned Mosaic runner now accepts an explicit experimental clock
mode and candidate installation. It records advances in the native-verified
recipe, logical emission times and diagnostic-only status. The opening two-step
note of M-LEN-001 is4.722ms short; later note durations match within1ns. M-PAT-001
passes in controlled time. Both affected cases pass with the default real-time
runtime. Exact evidence and SHA digests live in Mosaic's docs/testing/bugs.json
under transport-start-phase. No new Mosaic application fix was made.

The generic probe establishes absolute-sync semantics and supports investigating
Mosaic's immediate first lattice pulse. It does not establish the correct policy
for all internal/external transport starts, or complete clock-adapter fidelity.
Retain the failing exact-time oracle. Next checks include phase-swept starts and
restarts, tempo/reset and MIDI clock contracts, and all relevant mod/time sources
before the bounded Codex P5 review. Full manual coverage and C08–C15 remain open.
