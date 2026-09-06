# Generic application conformance fixtures

The C00 `boot.py` probe installs `probe-a` in a disposable code/data root. Its
literal rectangle, note bytes and controls test upstream API contracts.
`probe-b` is a second independently named application requiring the sibling
`probe-support` directory. C02 must run it via the generic loader, and C04/C11
must extend coverage to controls, params, persistence and reload. These fixtures
must never be renamed to Mosaic or depend on Mosaic libraries.

Creation is not acceptance: only probe-a has C00 runtime evidence at this point.
