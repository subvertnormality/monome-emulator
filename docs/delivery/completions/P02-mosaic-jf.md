# P02 progress: actual Mosaic Just Friends commands

2026-09-08, experimental; no downstream JF audio synthesis claim.

Optional fixture `fixtures/apps/nb-jf.lock.json` pins sixolet/nb_jf to
fc0922feb5f8e91f7732602a3b99716bf7099e78. Its source README and lib/mod.lua were
inspected. No root licence file was present; fetch externally, do not bundle its
source. Acquisition: `git clone https://github.com/sixolet/nb_jf.git
.runtime/nb-jf/source`, then verify the fixture pin before use.

`tests/mosaic_jf.py` maps unchanged Mosaic and nb_jf into an owned code root,
loads the mod normally, uses physical-style grid/key/encoder inputs and compares
the actual ii trace with independently calculated pitch and voltage encodings.
It selects mono voice 1, plays two four-note cycles and stops. No application
globals or upstream source are modified.

Retained failures:

- `artifacts/crow/mosaic-jf-20260908-165301/report.json`: selector recipe landed
  on JF MPE, which emits pitch/vtrigger rather than mono play_voice. The test
  timed out waiting for mono packets. MPE is an additional sorted entry; one
  further encoder step selects JF N 1.
- `artifacts/crow/mosaic-jf-20260908-165442/report.json`: actual mono pitch was
  correct, but the velocity oracle incorrectly used velocity/127. The explicit
  Mosaic step.lua note_on boundary uses (velocity-1)/126. nb_jf mono multiplies
  by 5 V; official Crow encodes 1638.3 units/V. The corrected expected formula
  allows only 1.1 integer units for quantization, not broad amplitude tolerance.
  Stop emits a mono release followed by all-voice release packets; both are valid
  documented JF trigger forms. The fresh rerun must pass before admission.

Combined candidate: `.runtime/mosaic-audio-01/installation.json`. This profile
keeps Mosaic external and is separate from the generic ii byte/limit/isolation
checks. Other Mosaic device profiles, broader audio reliability and review gates
remain open before tranche-1 commit/merge.

Fresh run `artifacts/crow/mosaic-jf-20260908-165705/report.json` passed two
four-note cycles with exact voice/address, quantized pitch/level expectations,
mono/all-voice release and successful owned shutdown/export. Full packets,
input recipe, runtime/application identity and native logs are retained.
