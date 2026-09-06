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

No identified in-scope defect may be put here as `later` if it prevents a required
acceptance row from passing.
| R10 | Scheduled MIDI holds the action lock for up to two seconds, delaying snapshots and browser heartbeats | fold:C07 | Real-time input scheduling must preserve client leases and measured responsiveness | P1; M1 uses immediate input, but timing acceptance may not waive this interaction. |
| R11 | MIDI prevalidation rejects isolated F7 and interrupted partial messages accepted by stock norns | fold:C10 | Native input boundary cases must align validation before full recording/mapping acceptance | P1; explicitly reported unsupported until verified. |
| R12 | Historical build-specific patch generators and spike duplicates remain in source tree | fold:C14 | Remove superseded or unsafe cache-mutating generators before distribution | P1; locked patches are the actual build inputs. |
