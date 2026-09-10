# Decisions

| ID | Decision | Basis |
|---|---|---|
| D01 | WSL2 release first; native Linux follows as a separate milestone | User, 2026-09-06 |
| D02 | MIDI behaviour only; no audible-output acceptance | User, 2026-09-06 |
| D03 | Cover all Mosaic software workflows; exclude physical Crow/Sinfonion and n.b. audio | User, 2026-09-06 |
| D04 | No manual tests and no real-device gate; LLMs must be able to act and observe programmatically | User, 2026-09-06 |
| D05 | Prefer actual norns runtime with a small hardware boundary adapter; prove feasibility before committing | Design proposal, C00 validates |
| D06 | Local versioned state and bounded Paranoia replace Parallax's issue/governance machinery | User requested proportionate adaptation |
| D07 | Provide API and browser UI using the same runtime event path | Default adopted after optional clarification; user can amend |
| D08 | Target existing Ubuntu 20.04 WSL first; prove incompatibility before proposing change; a contained newer userspace is an option, not a premise | User steering, 2026-09-06, supersedes earlier willingness to use a new distro |
| D09 | Every required software scenario has real-time runtime evidence; deterministic time is a later C16 enhancement and cannot block M0–M4 | P0 review correction |
| D10 | Pin and activate matrix/toolkit for documented MIDI modulation; capture Sinfonion software MIDI while excluding physical conversion | Source-verified P0 scope clarification, preserving all-software-workflows request |
| D11 | Product is a general-purpose norns/grid utility using official monome dependencies; Mosaic is an opt-in-installed fixture whose full applicable acceptance remains mandatory for release | User, 2026-09-06; supersedes any Mosaic-only product or hardcoded loader design |
| D12 | Runtime and application locks, installation, data and test layers remain separate; dependency updates require conformance and app regression evidence | Architectural implementation of D11; see UPSTREAM.md |
| D13 | Execute staged delivery, beginning C00 on the existing distro | User: “Execute”, 2026-09-06 |
| D14 | Use official C matron/crone release with real SC core and dummy JACK; native virtual-device event adapter | C00 empirical probe and runtime-decision.md; no Lua runtime replacement |
| D15 | Preserve native signed LED storage and official mext four-bit packing, including wrapped absolute values; retain coordinate bounds | C05 actual Mosaic playback exposed C03's stricter level rejection. `device_monome.c` stores int8/uint8 and pinned libmonome `mext.c:pack_nybbles` sends low nibbles. Patch 0010 and native level fixture amend the grid contract; P1 must include this correction in its runtime-boundary review. No Mosaic patch or weakened MIDI expectation. |
| D16 | Explicitly disclose emulator corrections of stock v2.9.4 realtime-byte parsing (0009) and cancelled queued clock resumes (0011) | Focused independent native probes justify these corrections for local development. They are not stock-hardware equivalence; capabilities and MIDI contract disclose differences. P1 includes them; C14 checks patch removal against the official update candidate. |

| D17 | Use dummy JACK's 1024-frame period at 48 kHz on the WSL host, retaining native frame time and scheduling | C07's isolated 128/512/1024 native probes measured -362.3/-4.2/-0.7 ms drift over ten seconds. The 128-frame profile suffered xruns. The corrected profile passes actual Mosaic swing and fractional lengths without changing timing thresholds. C12 still must pass ten-minute endurance. JACK 1.9.12 rejects its advertised long clock-source option; the system clock is already its default. |

Execution is authorized. No recurring jobs have been created.

D18 — User amendment, 2026-09-07: create the Mosaic checkout and dedicated
codex/behaviour-validation worktree/branch; push that branch. Mosaic owns a
complete manual-driven behaviour suite, including every function, edge cases and
potential failure modes, to find/fix bugs before a later refactor. Tests use
user-like inputs and user-perceived MIDI/grid/screen outputs. Bring controlled
time forward as needed for musical timing; retain real-time scheduling evidence.
This supersedes D09's defer-C16-until-after-releases scheduling, not its mandatory
real-time evidence. The emulator remains general purpose. Mosaic canonical plan:
/home/andy/projects/mosaic-behaviour-tests/docs/testing/BEHAVIOUR_PLAN.md.
# D19 — Codex-only future Paranoia reviews

User instruction, 2026-09-07: use only Codex for Paranoia reviews from now on.
The helper enforces this engine selection. Existing completed reviews remain
historical evidence; the bounded critique/follow-up budget is unchanged.

D20 — Fractional real-time timing metric, 2026-09-08: Codex arbitration
`01a07f14-57cb-7cb1-9f93-07c02f229e92` found that a newly added pointwise10 ms
interval/window gate was stronger than the established event-error profile,
without an independent musical basis. Extend the existing p99/max/final-phase
10/50/20 ms profile explicitly to each45-second fractional fixture, with the
population, percentile rule and verified independent deadline/origin mapping in
ACCEPTANCE.md. Implementation and fresh evidence remain required. Preserve the
old failed runs, exact controlled-time checks and mandatory ten-minute C12 gate.
This corrects a metric mismatch; it is not a waiver of measured host jitter.

The same arbitration rejects the new unit fixture's assumed nearest-half-down
rounding as an undocumented contract. Full-denominator musical windows and
bounded phase, supplemented by exact reset/no-reset invariants, replace that
assumption. Existing Mosaic rounding is unchanged; a separate rounding patch
would require evidence of a violated musical contract.


D21 — Opus-only future Paranoia reviews, 2026-09-10: supersedes D19 from this
point forward. The final Codex schedule-capacity follow-up had already completed;
retain it as historical evidence. Do not initiate another Codex review.

D22 — Norns-class performance qualification, 2026-09-10: performance is a
required pre-refactor delivery concern. Add automated constrained, deterministic
cost, real-time musical and comparative-regression lanes based on official norns
CM3/CM3+ facts. Do not claim x86 quota or QEMU wall time equals physical norns.
Toolkit/Matrix performance remains deferred with that optional integration.
