# Generic application conformance fixtures

The C00 `boot.py` probe installs `probe-a` in a disposable code/data root. Its
literal rectangle, note bytes and controls test upstream API contracts.
`probe-b` is a second independently named application requiring the sibling
`probe-support` directory. C02 must run it via the generic loader, and C04/C11
must extend coverage to controls, params, persistence and reload. These fixtures
must never be renamed to Mosaic or depend on Mosaic libraries.

The product-native probe-a adds parameter actions, explicit encoder sensitivity,
clock and metro cancellation and literal CC expectations. Probe-b checks sibling
include paths, controls and clock-driven note-off. error-init, error-coroutine
and error-hook deliberately exercise structured failure reporting. Run the C02
package with `python3 tests/native_loader.py`; its result records actual evidence.
