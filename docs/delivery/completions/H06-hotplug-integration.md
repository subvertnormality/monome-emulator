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
