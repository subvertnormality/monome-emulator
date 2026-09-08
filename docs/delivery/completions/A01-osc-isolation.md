# A01 progress: native audio and OSC isolation

2026-09-08; `artifacts/audio/osc-isolation-20260908-171112/report.json` passes
on `.runtime/audio-ready-01/installation.json`.

Two simultaneous native sessions use the unchanged pinned n.b./DoubleDecker
player. Native keys start a 440Hz voice in the first session while the second
remains silent. The second then plays 880Hz through its ordinary player bend;
both JACK captures retain their expected independent frequency. Closing the
first session leaves the second audible at 880Hz, and its Stop reaches silence.
All owned services close successfully and export their evidence.

The generic fixture optionally reads an external destination from an owned data
seed. On the same native key event it sends an OSC message to a test-owned UDP
listener. The exact address, type tags and float/string payload are asserted
against literal independent wire bytes in `external.osc`. This proves ordinary
non-57120 destinations remain intact while the player uses the session-local SC
route. It does not test arbitrary remote network reachability.

`tests/audio_osc_isolation.py` owns the listeners, seeds, session lifecycle and
PCM assertions. It does not modify installed mods or user applications.

Related Crow reliability: host-15 extends the existing instruction-hook deadline
to input callbacks and preserves an enclosing deadline for nested calls.
`artifacts/crow/serial-20260908-171423/report.json` passes eleven checks including
an infinite input callback. Blocking native/C calls are not covered by a Lua
instruction hook. Combined native regression and admission review remain before
tranche-1 merge.
