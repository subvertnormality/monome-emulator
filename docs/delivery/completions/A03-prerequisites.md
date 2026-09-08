# A03 prerequisites — optional Crow and sample imports

2026-09-08; implementation in audio-monitor, broader-tranche review pending.
No cheat codes source changes. Baseline sampler support is not yet a full A03 pass.

1. New per-session `crow_enabled=False` / CLI `--no-crow` skips the virtual Crow
   process/PTY. Actual native `norns.crow.connected()` returns false, capabilities
   say disabled, and all Crow capture/input/trace requests explicitly reject.
   Default enabled behavior remains intact. Two native presence cases pass:
   `artifacts/crow/presence-20260908-181736/report.json`.
2. Unchanged cheat codes with Crow enabled fails ii reads at startup:
   `artifacts/audio/cheat-codes-boot-20260908-181345/report.json`; preserve this
   unsupported optional profile. With explicitly absent Crow, unchanged boot and
   native key/frame checks pass at `cheat-codes-boot-20260908-181816/report.json`.
   No ii results were fabricated and no app version/source guard was changed.
3. New `audio_files` / repeatable CLI `--audio-file` snapshots selected files
   into the session audio root with streaming copy and copied-byte identities.
   Missing/duplicate inputs reject before overwriting targets. The generic
   official-file-picker test passes through native controls and actual audio:
   `artifacts/audio/file-import-20260908-182459/report.json` (5 checks). First
   session uses the real CLI; second uses the Python client. Both import the same
   basename from different file contents, then play 440/880Hz independently;
   first shutdown leaves the second playing. Host originals remain intact and
   identities are exported. Initial recipe `file-import-20260908-182220` selected
   tape/ because official util.scandir groups directories first; corrected using
   native E2 to select the sample, with no fixture/runtime UI override.

Run with `.runtime/tranche1-final/installation.json`. Native runtime binary/SC
sources are unchanged; the adapters belong to the current source identity.
Next is actual cheat codes file loading, pads, playback controls, live recording
and saved collection restoration through its UI, followed by virtual arc.
Broader ii reads remain explicit residual scope, not covered by no-Crow boot.
