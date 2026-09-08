# P02 progress: official Crow ii encoder and queue

2026-09-08, `codex/audio-monitor`; experimental, no default promotion.

`scripts/build_crow_ii_host.py` builds unchanged pinned Crow `ii.c`,
`l_ii_mod.c`, wrQueue and Lua with the official ii descriptor generators.
Copied source, generated headers, descriptors, adapter and executable hashes
are retained in the manifest. Source checkout identities and tracked cleanliness
are checked before building. A separate small host I2C boundary records outgoing
packets for the two JF addresses, 0x70/0x75. Reads, follower callbacks and other
module addresses fail explicitly. This is a standalone core probe, not yet a
native session capability or a downstream JF synthesizer.

Evidence: `artifacts/crow/ii-core-20260908-161203/report.json`, seven groups:

- Exact wire bytes for pitch/level, negative values, saturation and both addresses.
- All remaining JF write opcodes, covering all 14 commands in the pinned descriptor.
- Sixteen queued packets in order.
- Explicit failure on a seventeenth queued packet.
- Explicit failure on module reads, unknown commands and unconfigured modules.

The first candidate's overflow negative failed:
`artifacts/crow/ii-core-20260908-160956/report.json`. Compiler optimization
bypassed the printf macro interception and printed the errors while exiting
successfully. Candidate 02 uses linker wrappers for both printf and puts;
upstream files remain unchanged. The regression proves a failing process and
diagnostic for queue overflow. The final build log is empty (successful), and
all test subprocesses are terminal.

```sh
python3 scripts/build_crow_ii_host.py --generator-build .runtime/crow-host-10 --output .runtime/crow-ii-host-02
python3 tests/crow_ii_core.py --build .runtime/crow-ii-host-02
```

Build directories must be fresh. Next integrate the proven official ii core
with the existing serial/CV host and an owned session packet trace. Preserve
CV/input/clock regressions and use native script input to establish acceptance.
No hardware responses, address-reconfiguration state or JF DSP are simulated by
this recorder. A01 admission, actual Mosaic workflows, command deadlines and
EOF/reset semantics, clock/load qualification and broader apps remain open.
