# Delivery instructions

This is a local development tool, not a correctness-critical financial system.
Read `docs/delivery/PLAN.md`, `RUNBOOK.md`, `ACCEPTANCE.md`, and `state.json`
before execution. The cards define scope and dependency order. Resume using
recorded evidence, not conversation memory.

The product is a general-purpose norns/grid utility. Read
`docs/delivery/UPSTREAM.md`. Use official monome sources as pinned runtime
dependencies; keep adapters small and updates testable. Mosaic is an opt-in
acceptance fixture, never a core import, install requirement, hardcoded script
name, UI model, or runtime workaround. Generic conformance tests must pass with
Mosaic and all its dependencies absent.

Do not implement the emulator merely because you are asked to edit its plan.
Once delivery execution is requested, proceed through eligible cards without
routine approval questions. Respect actual tool permissions and user steering.

No manual testing or real hardware is an acceptance prerequisite. Run Mosaic's
actual application through the runtime input path. Unit mocks and internal state
inspection alone cannot establish workflow correctness. Never silently swallow
unsupported APIs, missing tests, dependency failures, or Lua errors.

Use Paranoia at the checkpoints and budget in the local runbook. Parallax's
runbook is source material, not this repository's operating policy. No mandatory
dual-vendor convergence, per-card mutation campaigns, or human certification.

Do not change upstream Mosaic to make an emulator test pass. A confirmed Mosaic
defect needs a minimal regression, an isolated candidate fix, and the explicit
baseline treatment defined in ACCEPTANCE.md. Never overwrite a user's project.
