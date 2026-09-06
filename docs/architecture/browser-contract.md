# Browser controls and observations

The session server serves `ui/` on its loopback port. Open `browser_url` from
`./dev/emu start`. Its fragment supplies the bearer token for observations and
actions; the token is not included in static assets. Cross-origin data requests
are rejected. This is a trusted local script development tool.

The screen uses the actual native Cairo 128×64 framebuffer. RGB channels are
already premultiplied against black and are presented opaque, avoiding a second
alpha multiplication. CSS scales with nearest-neighbour sampling. Grid levels
0–15 and device intensity remain distinct in the observable native state.

Keys use keyboard 1/2/3 or pointer holds. Encoder pairs Q/W, A/S and Z/X provide
negative/positive deltas; pointer buttons and wheel input use the same actions.
K1 tap enters/exits the native menu; K1 holds combine with other controls.
Multiple grid and norns keys may be held concurrently. Release, focus loss and
pointer cancellation send actual key-up events. A disconnected browser's lease
expires after 2.5 seconds. Its releases preserve inputs owned by other clients.

All actions use the same ordered, acknowledged native path as API scenarios.
Accepted and rejected requests are retained in `actions.jsonl`; native transport
inputs and output emissions are separately retained in `native-events.jsonl`.
Lua errors are visible and fail subsequent runtime requests.

Run `tests/browser_package.ps1` from Windows with the pinned Playwright/runtime
paths in that script. It starts four isolated WSL native sessions and uses
Chromium headless shell 151.0.7922.34, Playwright 1.62.1. Generic probe runtimes
have Mosaic and its fixture dependencies hidden in private mount namespaces.
Browser acceptance uses executable pixel, event, MIDI and LED assertions.
Headless focus-loss testing clicks into a separate iframe browsing context to
cause a real window blur; no synthetic blur event or visual judgement is used.

Each run has its own artifact directory and schema-checked manifest, bound to
emulator, app and runtime identities. Browser B evidence establishes control and
rendering behaviour; it cannot substitute for full Mosaic E/R workflow evidence.
