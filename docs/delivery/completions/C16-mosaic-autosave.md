# C16: Mosaic startup, autosave and mod-profile repeatability

Mosaic's authorised behaviour branch now owns M-SAVE-001 and an explicit
matrix/toolkit profile. The emulator core has no additional application imports.

M-SAVE-001 creates a pattern through physical inputs, waits for idle autosave,
closes its process, boots another native process from the actual saved data,
and checks restored LEDs and three full MIDI phrases. It passes in real time
and three fresh controlled repetitions. Input recipes, complete logical MIDI,
grid, framebuffer hashes and final clock/note state agree in both process
segments. The initial reload recipe accidentally toggled off the restored pattern
assignment; correcting that input made the unchanged output oracle pass. No new
Mosaic production fix was made.

The three controlled runs take22.528/22.172/22.402 seconds wall time, including
both native starts and cleanup, versus88.536 seconds real time. They advance64.93
logical seconds across their two processes. This is about3.95x faster for this
case, not a general performance guarantee. Comparison manifest:
`../mosaic-behaviour-runs/repeat-4ac65dde67a542b9afa2255edfc1647a/manifest.json`
relative to the Mosaic worktree's parent layout. Raw output stays in that separate
campaign storage; Mosaic's state.json records portable paths and SHA digests.

M-PAT-001 also passes with both pinned mods actually loaded, in real time and
three controlled repetitions with equal logical output. The profile requires
explicit external clean mod checkouts and records their exact revisions.
Comparison manifest:repeat-1833b336c02b48d69145b86a8c761e38 in the same storage.
This proves startup/coexistence, including the toolkit lattice and matrix deferred
bangs; it does not establish LFO/rhythm/macro routing or modulated MIDI correctness.

Next: physical-menu modulation routing and independent MIDI oracles, the open
transport-start-phase investigation, M5 admission gate and bounded Codex P5.
Controlled time remains experimental. Full manual coverage, T01 and C08–C15
remain incomplete; no Mosaic refactor has begun.
