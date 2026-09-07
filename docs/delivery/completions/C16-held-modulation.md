# Held modulation regression evidence

The external Mosaic suite now has nine named cases. M-MOD-003 reproduces a
second Matrix dependency defect: binding a route to an already-held macro does
not apply its current value. Both real-time and controlled baselines fail the
same MIDI pitch assertion. An explicit isolated dependency patch supplies the
missing depth argument and retains the previously verified clear-cache fix.
Neither Mosaic production code nor the original pinned mod checkout changed.

The held-source and pulse-LFO cases pass real time and three fresh controlled
processes each. Exact normalized input/MIDI/grid/frame/clock results agree.
The external suite records manifests and artifact hashes in its testing state:
held repeat `a7eb0af16e8345d0b3ddde9f4219ea53`, LFO repeat
`0d3e9748636549a59bcfde6f6cf99b30`, real-time held
`e6679ec529154c72b9730150ce4f5f62`, real-time LFO
`08bbd0b9072c41f9ae0a959026af2da1`. Child manifest and artifact hashes were
verified before recording results.

A reproduced oracle lifetime bug was also fixed: Cairo cached a scaled font
whose FreeType face had been freed. One font/library pair now lives for the
oracle process. A 1200-draw stability check and the native workflow regressions
pass. This was a test harness defect, not an application rendering defect.

Reproduction commands and exact patch identity live in the external Mosaic
branch's `docs/testing/progress.md`, `state.json`, and mod-patches manifest.
Controlled time remains experimental and diagnostic-only. M5/P5, the opening
transport phase discrepancy, full manual coverage and release stages remain
incomplete. These results do not establish a speedup for short interactions.
