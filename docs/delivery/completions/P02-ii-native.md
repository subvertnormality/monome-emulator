# P02 progress: native ii command recording

2026-09-08; experimental. Combined host `.runtime/crow-host-11` adds the
official ii encoder/queue to existing CV/input support. Candidate installation
`.runtime/crow-ii-native-01/installation.json` reuses the identified Crow-enabled
native runtime. No default promotion and no working demo changes.

Native launcher clears inherited ii trace configuration, then supplies an owned
exclusive `crow-ii.jsonl` path for this profile. Writes flush and fail on I/O
errors. The existing client exports JSONL evidence on close. The official Crow
Lua ii interface is loaded only when the compiled bindings exist. Queue work
drains after complete serial commands. Unsupported module reads fail explicitly;
this recorder provides no JF downstream DSP or hardware equivalence.

Evidence: `artifacts/crow/ii-native-20260908-161737/report.json` passes native key
input through norns/Crow serial to three exact JF packets, followed by explicit
unsupported-read failure. The earlier run `ii-native-20260908-161600` failed
because the test used `z` instead of the existing action protocol's `state`;
the protocol was preserved and the test corrected. Finalized cleanup assertions
were strengthened after that pass and require a fresh run before admission.

```sh
python3 scripts/build_crow_host.py --source .runtime/crow-feasibility/crow --ii-build .runtime/crow-ii-host-02 --output .runtime/crow-host-11
python3 scripts/prepare_crow_runtime.py --install .runtime/crow-norns-06/installation.json --crow-build .runtime/crow-host-11 --output .runtime/crow-ii-native-01
python3 tests/crow_ii_native.py --install .runtime/crow-ii-native-01/installation.json
```

CV/input/clock regression, bounded/timestamped public trace observation, restart
and isolation checks remain before admitting this device capability. Preserve
all A01 audio and actual Mosaic integration requirements. The newly authorized
desktop/Maiden/Docker tranche is queued after Mosaic reliability and broader
script support, as recorded in DESKTOP.md.

Follow-on evidence (host-12 / crow-ii-native-02):

- `artifacts/crow/ii-native-20260908-162313/report.json`: public API exact packets,
  monotonic timestamps, cursor continuation, unsupported reads and strict cleanup.
- `artifacts/crow/clock-native-20260908-162359/report.json`: native clock regression.
- `artifacts/crow/ii-limits-20260908-162531/report.json`: all 100,000 packets retained
  in order, next packet fails; exclusive trace creation preserves existing data;
  two fresh hosts reset sequence and isolate records.
- `artifacts/crow/serial-20260908-162642/report.json`: serial framing and unsupported
  operation regressions with the ii-enabled profile.
- `tests/crow_ii_trace.py` passed partial writes, pagination, bad cursors and
  oversized record tests. API contract: `docs/architecture/crow-ii-api.md`.

Host-11 input regression is retained in
`artifacts/crow/input-api-20260908-162045/report.json`. Native simultaneous-session
isolation is still separate from the host restart checks above. Command EOF and
Lua deadline changes are being built as host-13, not claimed by host-12 evidence.

Host-13 follow-on:
`artifacts/crow/ii-isolation-20260908-162958/report.json` passes two simultaneous
native sessions, bidirectional trace isolation, continued output after stopping
the other session, a fresh third session with reset sequence and clean shutdown.
Candidate is `.runtime/crow-ii-native-03/installation.json`.

Mosaic inspection identified its normal voice-selection setup call
`crow.ii.pullup(true)` in unchanged `channel_edit_page_ui.lua`. Host-14 binds that
boolean/integer API to official `ii_set_pullups`; the host's existing I2C state
stores the setting. This is virtual bus configuration, not electrical hardware
emulation. A fresh candidate and native test cover this setup call before notes.
The source convention is pinned Crow `lualink.c::_ii_pullup`. Actual Mosaic
workflow acceptance still requires the external n.b. voice mod to be pinned and
loaded through the normal mod lifecycle; the core n.b. fixture only has its
base player library. Do not pretend its tested-player name list installs mods.
