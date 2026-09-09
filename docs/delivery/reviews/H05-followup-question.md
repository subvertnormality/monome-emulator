Focused follow-up to H05-raw.json, session01a08641-8f92-7152-9ac6-1bd3809feb98.
Review only fixes for the two code/acceptance majors, not another whole branch.

Both Dockerfiles now declare BuildKit TARGETPLATFORM, reject wrong target and
runtime dpkg architecture before apt, and pass the target to verify_packages.py,
which checks it against lock.platform before exact inventory. An actual baseline
amd64 context built with --platform linux/arm64 produced a falsely arm64-labelled
image; fixed context12 rejects that mismatch in the first RUN, while matching
amd64 builds successfully. See H05-fixes-evidence.json and retained logs. Unit
faults reject target/runtime mismatches and accept matching profiles.

The JACK diagnostic now starts a named detached container, requires activated
real JACK client connections and advancing frame time throughout a ten-second
window, then stops it and requires exit0. Timeouts fail. Client JSON uses a
unique marker amid retained native logs. Failure containers are stopped/retained;
successful ones removed. Six real variants passed with42 client connections.
Tests reject Docker startup timeout and a running container with no JACK client.
The initial mixed-stdout parsing failure is retained as false, not reclassified.

Confirm whether these close the two code findings; report any concrete remaining
problem narrowly. No runtime DSP/input/lease changes after the six passing Windows
host gates. The rebuilt matching image also has a native cancellation/reopen smoke.

The third finding remains an explicitly open Mac evidence gate. The user notes
that reports are on another machine. Final hash/result inspection can run there;
no local Mac report is claimed inspected here, no absent file is counted as proof,
and no main merge/platform admission is being requested by this query. Do not
spend this follow-up repeating that known external gap as a new code defect.
Do not modify files or run native tests. Trusted single-user development utility,
no hardware prerequisite, enterprise threat model or interactive latency promise.
