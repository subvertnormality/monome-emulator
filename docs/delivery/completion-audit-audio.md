# Audio/device goal completion audit — 2026-09-09

Main and audio-monitor are at e201859 before this audit. The preceding goal turn
was progress: a fresh combined WSL candidate was built and seven integration
reports passed. This audit does not mark the full goal complete.

| Requirement | Current evidence and disposition |
|---|---|
| Mosaic audio/devices first, commit/merge before broader work | A01-tranche1.md records reviewed admission and merge4b7ab6b; A02-A03-P03.md records subsequent reviewed stage2 merge4c9cb8b. Main includes both. |
| Real supported engine, actual capture and signal assertions | A01 and H01 native PCM/sink/Windows endpoint evidence; A04 same-candidate generic audio and unchanged Mosaic/n.b. capture passed. No arbitrary-engine claim. |
| Investigate audible clicks and continuity | A01 renderer tests, H01 retained25-sample endpoint dropout and strict dropout oracles, H03 every-sample browser continuity/negative cases, H04 endurance and diagnosed JACK shutdown race. Investigation performed; original clicks are not all conclusively localized and unlimited stability is not proven. |
| Crow and related device capabilities useful to Mosaic | P01/P02 official firmware/serial/CV/input/clock/JF trace subset, plus A04 native14-check/2000-callback regression. Downstream JF synthesis, ii reads and electrical equivalence are explicitly unsupported. |
| Broader scripts such as cheat codes2 | A02-A03-P03 sampler, reverse/loop, retained live recording, fresh-session collection restoration and optional arc evidence; A04 unchanged sampler/arc integration passes. No claim for every mapping or third-party engine. |
| Reference architecture, pinned official sources, licensing and patches | H00.json and H00.md record inspected repositories/commits/files and licensing; runtime remains official monome. Patch README and H04 evidence record official bases, inspected upstream, hashes and removal conditions. No reference fork replaced official sources. |
| Real desktop audio | H01 admitted WSLg and Windows endpoint software boundaries; A04 selected sink and owned routing/restart/isolation pass. Physical speaker output is not claimed. |
| Official Maiden editor/REPL, restart and isolation | H02 reviewed file-tree edit/run, Lua/SC REPL, fault recovery and session-isolation evidence. A04 repeated eight actual editor/audio/cleanup checks on the refreshed WSL build. |
| Browser audio, reconnect, cleanup and latency | H03/H04 actual renderer tests and native cleanup; final H04 two-minute/rate windows pass. Measured p95176.9/162.1ms is above150ms target and supports delayed monitoring only. |
| Optional Docker, editable scripts, persistent data, generic controls/grid/MIDI | H04 admitted Windows-host/browser gates, data-root lease/reopen, startup cancellation, errors and exact native cleanup. Current image built from434c2da; H04 reviewed/merged436b05c. |
| Preserve WSL, native input contract, app independence and concurrent work | A04 builds a separate candidate; current install unpromoted. Generic fixtures and Docker runtime-only evidence have no mandatory Mosaic dependency. Main's state.json and two untracked Mosaic progress files remain outside this work's changes. |
| Independent Windows/macOS validation, Apple Silicon where available | Windows has actual host evidence. macOS remains not_run: no accessible host. Only local Windows named-pipe Docker contexts exist, rechecked this turn. Apple Silicon and native Linux lanes are also not_run. See PLATFORMS.md for six commands and required evidence. |

This turn recomputed every listed SHA256 and checked actual report status in
H04-evidence.json (25 reports, including retained failures) and A04-evidence.json
(7 passing reports). No report was rerun or reclassified. Existing review and
completion records establish their named scopes, not a universal release or the
independently owned full Mosaic behavior campaign.

## External dependency and resumption

The unavailable-host condition was recorded in the H04/H05 goal turn, remained
after the next A04 goal turn, and was rechecked in this third consecutive goal
turn. Useful available-host work continued in the preceding turns; it is now
complete for the queued cards. No live owned runner is awaiting observation.
Repeating Windows tests cannot establish Mac compatibility.

Resume H05 with access to a macOS Docker/Chromium host, and Apple Silicon where
available. Run the documented host suite against the identified image, retain
actual host/mount/audio/latency/cleanup results, and diagnose failures before
admission. Native Linux has its own independent lane. No remote host, paid CI
allocation or platform support was invented. The full goal remains unfinished
and is blocked on host access, not marked complete.
