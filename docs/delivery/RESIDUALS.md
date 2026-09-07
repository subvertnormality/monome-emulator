# Residuals

| ID | Impact | Disposition | Owner / promotion condition | Reason |
|---|---|---|---|---|
| R01 | n.b. sound engine/audio compatibility | later | Future audio scope requested | Explicitly outside MIDI-only release |
| R02 | Physical Crow, Sinfonion, grid USB and external MIDI hardware integration | later | Future physical-device integration requested | No real hardware needed for this delivery |
| R03 | Exhaustive compatibility certification for every third-party norns script | later | A named additional script becomes a full compatibility target | General-purpose loading and native API conformance are required now; universal audio/hardware/script coverage is not claimed |
| R04 | Physical I/O, temperature and network-manager warnings; service-management side effects | fold:C02 | C02 before product readiness | Native host profile needs explicit absent/unsupported handling and safe process lifecycle |
| R05 | Spike has one grid orientation and one MIDI message-event port | fold:C03/C05 | C03 grid and C05 MIDI conformance | Native boundary feasibility proven; stream/multiport/reconnect contracts still required |
| R06 | Adjacent official update ref not built | fold:C14 | C14 real update/rejection/rollback acceptance | Ref and diff inspected only; cannot claim upgrade compatibility |
| R07 | matrix/toolkit root license files absent | fold:C14 | Packaging; never bundle unidentified fixture source | Separate opt-in source fetch preserves runtime/app boundary |
| R08 | Mosaic adjacent equal pitches emit repeated note-ons with aggregated note-offs; strict counted capture reports remaining note 65 after stop | fold:C12 | A18/A22 panic/overlap package must classify receiver semantics and, if defective, isolate a candidate Mosaic fix before release | Discovered during C06 exploratory E4→F4 edit next to F4. Native trace in `artifacts/c06/api-development/` retains mismatch. C06's independent four-pitch slice uses E4→G4; no tracker relaxation, xfail or release exclusion is permitted. |
| R09 | One Windows browser read failed during simultaneous API/browser native suites; native process remained healthy and isolated browser rerun passed | fold:C12 | Reliability/endurance and concurrent-client checks must diagnose or reproduce/resolve before release | Failed package `artifacts/c06/da15eb28c8ab4c0e8d69a7d18420e19c`; browser request-failure logging added. No uncertain action was retried and no failed package is accepted. Current M1 browser evidence is an isolated run, not a concurrent-browser reliability claim. |
| R10 | Scheduled MIDI previously held the shared observation lock for up to two seconds | resolved:C07 | Separate action serialization allows native snapshots and heartbeats during the wait | Two actual future MIDI requests preserve held input and event order while 14 snapshot/heartbeat pairs stay responsive. Failed scheduling remains explicit in the action trace. |
| R11 | MIDI prevalidation rejects isolated F7 and interrupted partial messages accepted by stock norns | fold:C10 | Native input boundary cases must align validation before full recording/mapping acceptance | P1; explicitly reported unsupported until verified. |
| R12 | Historical build-specific patch generators and spike duplicates remain in source tree | fold:C14 | Remove superseded or unsafe cache-mutating generators before distribution | P1; locked patches are the actual build inputs. |
| R13 | First SIGTERM arriving during native close can interrupt its cleanup loop | fold:C11 | Lifecycle interruption tests must cover close already in progress | P1 follow-up residual; ordinary owned startup failure and stop cleanup pass. |

| R14 | Python warns when the server Popen object is collected after intentional asynchronous startup handoff | fold:C11 | Retain/reap the owned server handle and verify repeated lifecycle cleanup | Native service groups currently stop cleanly; the warning is retained in test logs and must not be confused with proven orphan-free parent-process lifecycle. |

No identified in-scope defect may be put here as `later` if it prevents a required
acceptance row from passing.

R15 — Stopped scale-slot highlight: fold:C12 (A19). Native failed evidence artifacts/c08/7af59ee065a04cd9a23e1404d477c631/manifest.json shows default slot1 LED2 after stopping and shift-editing slot16, whose edit-only LED4 is correct. scale_edit_page.lua's playing draw sets the fader to0 and stopped drawing does not restore it. Preserve/reproduce the active highlight assertion in the C12 display-refresh package; current scale controls package verifies selected edit-only indicators and MIDI, and earns no credit for this missing highlight. Do not waive A19.
