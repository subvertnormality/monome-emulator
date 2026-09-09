# H06 — Hotplug integration with audio and arc

Implementation authorized after inspection of origin/codex/hotplug-admission
at 801fcdc, with main at eb6c427. Work remains in codex/audio-monitor; concurrent
main delivery changes must remain intact. Status: integration in progress.

The branch's MIDI input 12 and output 18/19/20 overlap main's optional arc
input 12/13/14 and output 18/19. Preserve the reviewed hotplug protocol and its
historical evidence. Assign arc input 16/17/18 and output 24/25 in the rebuilt
combined runtime and host adapter. The new lock requires a rebuilt installation;
do not relabel or reuse an old candidate against changed source identities.

Preserve main's native action deadlines, JACK lifetime/large-period fixes,
Crow/arc options, official sources and session isolation. Retain the branch's
optional SDL/screen teardown patches and installation-owned library prefix.
No application-specific workaround or public action schema rename is required.

Acceptance before main integration: focused MIDI connection, scheduled evidence,
clock-admission and arc contracts; reconstructed locked patch application;
native hotplug and arc/audio checks on one identified combined installation;
strict teardown and explicit unsupported old-runtime behavior. Recheck Docker
source build compatibility because the runtime lock changes. Run one scoped
Codex medium/600-second integration review, with at most one focused follow-up.
Update user-facing generic protocol and installation instructions and record
actual commands/results here. Do not claim existing old-source admission passes
establish admission for the combined source.

Merge checkpoint 50c8d1e resolves all three textual conflicts and the wire-ID
collision. Dedicated imported evidence receipts are retained; shared state.json
was deliberately kept from main to preserve its independently owned campaign.
README now describes the already merged native Apple Silicon Docker profile.

Rebuilt .runtime/h06-locked-01 from the current official lock using the verified
existing prefix, then .runtime/h06-audio-01 with --arc, --crow-build
.runtime/crow-host-16, --large-jack-period, --sdl-ownership and
--screen-worker-shutdown. The audio build accepts --reference-install so no
current installation is overwritten. .runtime/h06-tools-01 adds capture/monitor.

Focused checks passed: 11 clock-admission tests, 10 MIDI connection tests, 3 arc
contracts. Syntax compilation passed. Actual runtime acceptance:

- tests/arc_native.py --install .runtime/h06-tools-01/installation.json --hotplug:
  9 checks passed, including MIDI-disconnected arc delta/LED/key release,
  independent arc reconnect, resumed MIDI sends and two-session isolation.
  Report: artifacts/arc/native-20260909-161513/report.json.
- tests/midi_hotplug_native.py --install .runtime/h06-tools-01/installation.json:
  passed; artifacts/hotplug/runs/f6034fbc29e54648b1700ddae1d8c8de/result.json.
- tests/audio_capture_api.py --install .runtime/h06-tools-01/installation.json:
  10 checks passed, actual retained PCM, channel routing, silence negative,
  cancellation/restart/shutdown. artifacts/audio/capture-api-20260909-161703/report.json.

Committed Docker context .runtime/docker-context-h06 exports 50c8d1e. Windows
amd64 image monome-emulator:h06-01 built successfully; full log retained at
artifacts/docker/build-h06-01.log. Host smoke and slow-stream checks are in progress.
The new merged source is not claimed to have repeated Mac or full M5 admission.
