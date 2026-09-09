# H06 integration review

Critique 01a086c0-9132-7882-b2d1-48252b958e0a inspected merge50c8d1e and
native combined evidence. Arc IDs, shared deadlines, capture framing/history and
real audio evidence were consistent. One major finding accepted: scheduled MIDI
sampled actual time before waiting for midi_connection_lock, hiding contention
from lateness evidence.

Patch0013 and its generator now sample inside the mutex immediately before
connection determination and delivery/drop. The lock hash changes explicitly;
existing installations are not relabelled. Actual functions extracted unchanged
from reconstructed baseline/fixed emu_bridge.c compile in
tests/midi_arrival_contention.py with real pthread mutex contention. A semaphore
proves the native function attempted the held mutex before a 250ms delay; both
connected delivery and disconnected drop must timestamp after release. Baseline
fails both; candidate passes both. This is a focused native C boundary regression,
not a claim of whole-runtime behavior from mocked transport callbacks.
Report: artifacts/hotplug/arrival-contention-20260909-162712/report.json.

The full 78-contract suite passed in266.570s before the one-line native timing
correction, with previously observed subprocess/file ResourceWarnings retained.
Combined runtime hotplug, arc, capture, slow stream and Windows Docker/browser
checks passed before correction. Corrected locked/audio rebuild and focused native
hotplug/arc/audio checks follow; no full M5 or new Mac claim. One focused review
follow-up is reserved for the timestamp fix and its regression evidence.

Follow-up01a086c9-2792-7a01-ae79-7ef6de8ea943 closed the timestamp finding after
inspecting source, lock/hash identity and baseline/fixed C results. Corrected
whole-runtime hotplug, arc and audio capture plus Windows Docker startup/browser
checks subsequently passed; H06-final-evidence.json records their identities.
No remaining substantive finding; review budget closed.
