# A01 progress: actual Mosaic audio integration

2026-09-08, experimental `codex/audio-monitor`. Not admitted.

`tests/mosaic_audio.py` maps unchanged pinned Mosaic and DoubleDecker into an
owned optional code root, loads the mod normally, and drives the existing
four-note native input recipe. It captures actual JACK audio before playback,
during the pattern and after Stop. No application globals or source patches
are used to select the voice. With the minimal MIDI fixture plus DoubleDecker,
Mosaic's alphabetical device list puts its built-in CC Device between None and
DoubleDecker. The standard recipe selects CC Device; one additional E3 step and
K3 commit select DoubleDecker.

First run failed before playback:
`artifacts/audio/mosaic-20260908-163731/report.json`, session
`72bd9f58649b4323b43270327acfee6c`. SC reported a failed temporary sound-file
write and nil `bufnum` in DoubleDecker.dynamicInit. All processes shut down
cleanly, as retained in the session cleanup.json.

Inspection found a composition gap: the Crow candidate reconstructed the base
audio runtime but did not contain the already-tested default-server SC adapter
from A01-nb-player. Server.default therefore remained different from the active
Crone server. `scripts/prepare_audio_mod_runtime.py` is being applied to
crow-ii-native-04 as `.runtime/mosaic-audio-01`; this uses the existing declared
patch and retains official runtime source identity and the Crow profile. This
diagnosis still needs the unchanged integration rerun; do not claim success
from finding the missing adapter alone.

Mosaic pin: 160d1ea7506773e65f298094e11d005dcb568dff.
DoubleDecker pin: 8729b9ceee71d2b07067e89fbef5d8b98d6a0c89.
The source n.b. dependency remains the pinned Mosaic submodule. Broader engine,
device, click/reliability and admission obligations remain open. Before tranche
1 merge, the canonical candidate build must compose all required adapters so
future rebuilds cannot silently lose the audio mod configuration.

The combined candidate completed and fixed startup: second run
`artifacts/audio/mosaic-20260908-164300/report.json` had no SC initialization
error, but its actual capture was silent. Recorded framebuffer diagnosis showed
CC Device selected. This was a test recipe error, not audio proof. The corrected
recipe adds one E3 step and K3 after `configure()`, and is being rerun unchanged
otherwise. The first ordering assumption above was corrected from this evidence.

The canonical audio candidate builder now calls the same default-server patch
function as the existing SC-only preparation tool and records its digest in the
manifest and complete build patch. This source change still requires full fresh
build verification before admission; the combined runtime is its current
functional integration evidence.

Third run `artifacts/audio/mosaic-20260908-164619/report.json` produced real
pattern audio (RMS 0.03854; C4/D4/E4/F4 energy fractions 0.1516/0.0852/0.1102/
0.1225), then failed its three-second stop-window assertion. Analysis of the
saved tail in 250ms windows showed decay from 0.000310/0.000236 RMS to
0.0000618/0.0000594 RMS. That supports an effects-tail diagnosis, not a sustained
voice. The test now captures six seconds immediately after Stop and requires
the final measured window to satisfy the same absolute 0.0001 RMS threshold.
It retains the full decay waveform. A fresh run is required; no pass is claimed
from the earlier partial result. This scoped test proves audio at the phrase
frequencies, not exhaustive note-order/timing or all Mosaic workflows.

Fresh run `artifacts/audio/mosaic-20260908-164814/report.json` passed baseline
silence, actual phrase-frequency audio and post-stop effects-tail release, with
successful owned shutdown/export. Candidate `.runtime/mosaic-audio-01` combines
Crow host-14 and the default-server adapter. Full native input recipe, source
identity, raw JACK WAVs and cleanup are retained. This is the current scoped
Mosaic audio evidence; all earlier failures remain available.
