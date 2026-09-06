# Monome emulator for Mosaic development

This repository currently contains the delivery plan, not a working emulator.
The target is autonomous development and verification of Mosaic without a real
norns or grid, with WSL2 delivered first and native Linux subsequently.

Start with [the execution plan](docs/delivery/PLAN.md). It links the staged cards,
[acceptance contract](docs/delivery/ACCEPTANCE.md), and the proportionate
[delivery runbook](docs/delivery/RUNBOOK.md).

MIDI behaviour is in scope; audible output, n.b. audio engines, and physical
Crow/Sinfonion integration are outside the first release. Acceptance is fully
automated. Existing Mosaic unit tests supplement runtime and UI acceptance.

`upstream/mosaic/` is a local inspection checkout, not vendored application code.
The implementation must acquire pinned dependencies reproducibly.
