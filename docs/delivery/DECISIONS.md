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

Execution starts only when requested. This planning task does not launch an
unattended implementation campaign or create recurring jobs.
