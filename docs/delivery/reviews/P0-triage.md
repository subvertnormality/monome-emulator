# P0 plan review and corrections

Status: complete. First-pass substantive findings corrected; the focused Paranoia
follow-up reported no remaining in-scope blocker or major. Its two minor
clarifications are incorporated below. No further review round is required.
This is a one-shot structural Paranoia review, not tracked convergence or runtime
validation. External host/build premises remain unverified and owned by C00.

Source response: `P0-attempt-2.json`, engine Claude, session
`43d00778-43b3-4a5d-95ff-2426ec3ec003`. The response record contains exact reviewed
input and its digest. First launch (`P0-raw.json`) failed with exit 127 because
the non-login WSL PATH omitted the installed Claude CLI. The diagnosed retry used
a login shell and completed. The review's statement that two calls had failed was
based on reading the second call's still-running record, not a second failure.

| Finding | Disposition | Correction / evidence |
|---|---|---|
| Deterministic adapter unnecessarily gates all workflows | Accepted | C07 now owns real-time semantics/replay only; C16/M5 adds controlled time after M3/M4 releases. V07 cannot block M0–M4. |
| D-only tier assignments could produce a false green release | Accepted | Every required software scenario requires E; each A01–A22 family needs E/R; C01 and release-check reject D-only/mock-only coverage. A23/A24 are explicit platform gates. |
| WSL virtual MIDI feasibility is discovered too late | Accepted | C00 requires actual vport enumeration, outbound capture and inbound callback, including ALSA/kernel capability probe and smallest native alternative if needed. |
| Modulation depends on unowned external mods | Accepted and source-verified | README links matrix/toolkit. C00 pins dependencies; C02 installs/activates real mod profiles; C09 verifies MIDI effects on Mosaic parameters for both paths. |
| Mosaic unit runner can exit 0 after skipping | Accepted and source-verified | C00 isolates the runner from conventional installed norns path, parses luaunit totals, requires >0 tests and rejects skip banner irrespective of exit code. |
| Sinfonion exclusion conflates physical conversion with MIDI | Accepted and source-verified | C05/C10 test virtual Norns2sinfonion program changes; only physical receiver/conversion remains excluded. |
| Mosaic has no device-wait readiness state | Accepted | C02 defines readiness from init return, live clocks and first script frame; device capabilities are separate. |
| P0 artifact needed a precise completion definition | Accepted clarification | C00 depends on completed Paranoia response plus this substantive disposition record, not a particular engine. Transport error is never review evidence. |
| Autosave and random splash frames can pollute tests | Accepted | Separate first/autosave boot fixtures; explicit autosave timing/splash assertions in C06/C12; no broad frame masking. |
| Source include paths require full dust-root isolation | Accepted and source-verified | Per-session dust root, each candidate mounted at code/mosaic, _path/state.path coherent; C02/C11. |
| Device configs must be present before init | Accepted | C06 seeds config before start. Malformed config checks diagnostic plus absent selection. Source actually prints `Error: JSON is invalid:` at device_map.lua:26, so no blanket error-message waiver is needed. |
| Pulse rounding could be mistaken for scheduling error | Accepted | C07 computes native ppqn/note-off rounding independently, retains unrounded intent and expected dispatch, then measures scheduler error. |
| Pinned browser runner may be incompatible with Ubuntu 20.04 | Accepted as unverified premise | C00 must actually run browser automation fixture. A Windows runner is an available architecture choice; no distro upgrade presumed. |
| n.b. “Mods and Software Devices” needed explicit disposition | Clarified exclusion | Audio engines and physical Crow/JF/Ansible paths remain excluded by D03/R01/R02. device_map.lua drops nb midi players from the device list; native Mosaic MIDI remains fully covered. C00 still enumerates exclusions individually and must surface any newly discovered in-scope dependency. |
| A20/A21 E-evidence labels needed concrete meaning | Accepted follow-up clarification | A20 uses independently rerun real-runtime Mosaic suites; A21 uses a real Mosaic coroutine-error injection with expected failure/trace, not a mock crash. C01 verifier enforces these contracts. |

Additional local refinement: C13 repair agents receive squashed seeded snapshots,
without an uncommitted seed diff or solution history that reveals the bug location.
Milestone applicability now names exact family ranges so C12 does not accidentally
depend on future C13/C14/C15 evidence. M2 is A01–A19 plus A21–A22; later gates add
the LLM proof and platform delivery families.

Follow-up: `P0-follow-up.json`, Paranoia query, engine Claude, session
`d00a0e1b-1327-43a8-b4e7-252a6eb4061f`. The reviewer found no in-scope blocker/major.
The follow-up also notes that the autosave splash flag may be set/cleared
synchronously without a rendered splash; the contract requires observed
documented behaviour, not invention of a transient frame. Runtime probes resolve
the actual sequence. Two substantive reviewer calls were used (one critique,
one focused query), plus one failed launch before review began.

No user scope was reduced. All documented MIDI/software workflows remain in scope;
virtual time is an added optimisation, and the core real-time release is independent
of its feasibility. No code/runtime card is complete.
