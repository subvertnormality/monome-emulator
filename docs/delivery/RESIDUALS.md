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

No identified in-scope defect may be put here as `later` if it prevents a required
acceptance row from passing.
