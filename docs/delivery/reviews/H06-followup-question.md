Review only the accepted scheduled-arrival timestamp finding from session
01a086c0-9132-7882-b2d1-48252b958e0a. No new cold whole-project review.
Patch0013 and prepare_midi_hotplug now place the actual timestamp inside
midi_connection_lock, immediately before connection determination/delivery/drop.
The dependency lock hash was updated; current.json and old candidates preserved.

Read tests/midi_arrival_contention.py/.c and the actual retained report/logs at
artifacts/hotplug/arrival-contention-20260909-162712. The test compiles the exact
scheduled_midi function extracted from baseline and fixed reconstructed sources;
real pthread_mutex/sem synchronization forces a 250ms contention interval. Both
connected and disconnected branches must report timestamps after mutex release;
baseline fails and candidate passes. Transport callbacks are stubs, so this is
explicitly a native C boundary regression, not whole-runtime acceptance. Existing
real-runtime hotplug and audio tests separately cover dispatch and lifecycle;
corrected build checks are recorded in H06-hotplug-integration.md as they finish.

Does this resolve the concrete timing-evidence defect without changing logical
clock semantics, delivery/drop order or existing deadlines? Inspect actual source
and evidence. Identify only concrete remaining issues in this fix. Budget is one
focused Codex medium600s follow-up; no hardware or artifact-transfer gate.
