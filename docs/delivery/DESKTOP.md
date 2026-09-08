# Desktop, Maiden and optional container delivery

Authorized 2026-09-08; supplements AUDIO.md and overrides historical MIDI-only
scope. Implementation is authorized after concrete card preparation and the
local review checkpoints. WSL Ubuntu 20.04 remains the primary working path.
This queue supplements the active Mosaic audio/device and broader script goal.

## Ownership and existing evidence

Worktree inspection: main at 319e3a0 owns the Mosaic campaign; audio-monitor at
319e3a0 owns audio/device work; codex/midi-hotplug at 859b8b5 and detached Linux
validation at bdf97b6 also exist. Recheck status before cross-cutting edits.
Preserve their work and the existing browser demo. This worktree records progress
in audio-state.json; do not overwrite the concurrent main state.json campaign.

Existing A00/A01 evidence covers real norns/JACK/SC synthesis and WAV capture,
external engines and one n.b. player, plus browser PCM rendering. These are
experimental scoped results, not proof of direct host output or all engines.
Reuse launcher isolation, browser controls/framebuffer/grid, MIDI and automation.

## Cards and dependencies

| Card | Missing capability and smallest integration | Automated acceptance |
|---|---|---|
| H00 reference audit | Inspect winder/norns-dev and schollz/norns-desktop Dockerfiles, services, startup, audio routing/streaming and runtime diffs at recorded commits. Check official upstream for existing fixes. Record licences before copying any code. | Reproducible inspected commits/file inventory, patch comparison and attribution decisions. Repository claims are hypotheses, especially external-device support. |
| H01 direct desktop audio | After H00, add an opt-in owned route from existing JACK output to the available WSL/Windows audio sink. Reuse real official norns/SC, existing capture and lifecycle. | Generic supported engine, measured frequency/RMS and routing; sink-boundary capture where available; start/stop/restart, isolation, missing-sink failure and cleanup. Distinguish engine, transport, browser and audible host boundaries. Manual listening is not a gate. |
| H02 official Maiden | After H00, pin official Maiden and integrate its editor/REPL with launcher-owned sessions, ports and lifecycle; disposable editable project only. | Browser automation edits and runs a generic script; changed runtime output and REPL reply; two-session switching/restart, data/project isolation and cleanup. Never overwrite user projects. |
| H03 portable browser audio | After H01 routing assessment, extend existing PCM/worklet path only where needed. Avoid a second controls/screen implementation. | Actual runtime signal at browser renderer; disconnect/reconnect, stale-stream rejection, cleanup and measured end-to-end latency. State monitoring versus interactive suitability from measurement. |
| H04 optional Docker baseline | After H00 and launcher contract audit, build pinned official sources and reuse existing launcher/browser/automation. Editable host code mount, persistent data mount, owned processes. WSL path remains available. | Container generic script startup, browser controls, virtual grid, exact MIDI capture, editable code reload, data persistence, restart and cleanup. Pin image/build inputs and record host/container architecture. |
| H05 platform matrix | After H04, validate Windows and macOS separately, Apple Silicon where available. Investigate H03 browser route for portable output. | Per-host startup/control/grid/MIDI/audio/latency/mount/cleanup evidence. Linux-only container success cannot admit Windows/macOS. Unavailable host remains not_run, with reproducible runner instructions. Document physical USB/MIDI/grid/audio limitations individually. |

User queue correction, 2026-09-08: all H00-H05 work follows completion of reliable
Mosaic audio/device capabilities (including audible-click investigation), then
broader script support such as cheat codes 2. Do not switch after only the Crow
ii checkpoint. Within this later tranche, priority is H01, H02, then H03;
H04/H05 are optional distribution work, not a replacement runtime. Preparatory
queue documentation is not permission to bypass the earlier tranche.

H00 must populate for each priority: existing evidence, concrete capability gap,
adaptable architecture/configuration, smallest session-compatible implementation,
and actual-feature test. Review this expansion with the runbook's Codex Paranoia
medium/10-minute budget, one critique plus focused follow-up. Review integration
at admission using the same budget; no mandatory human/hardware certification.

## Source and licensing boundary

References: https://github.com/winder/norns-dev and
https://github.com/schollz/norns-desktop. Initial README inspection confirms these
need deeper source inspection; inspected source commits are pending H00, not
invented from a web page. Winder declares GPL-3.0: architectural ideas may inform
independent integration, but no source is copied into this MIT project without
an explicit compatible licensing decision and attribution. Inspect Schollz's
licence too. Keep official monome runtime pins. Any required borrowed runtime
change is an explicit patch with official base, rationale and removal condition.

Deliver working eligible features, automated evidence, user instructions,
reference/attribution notes and exact limitations. This document is a queue and
acceptance contract, not evidence of implementation or platform support.
