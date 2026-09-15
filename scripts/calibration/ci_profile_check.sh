#!/bin/bash
# Cross-host profile check inside the emulator image:
#   docker run --rm --user root --shm-size 256m -v "$PWD/out:/out" --entrypoint bash <image> \
#     scripts/calibration/ci_profile_check.sh [profile.json]
# Builds the opt-in profile runtime, runs the generic probe unprofiled and
# profiled (3 fresh sessions each) and applies the fail-closed profile check.
# The unprofiled verdict is expected to fail and demonstrates the check detects
# a runtime that does not model the device.
set -u
PROFILE=${1:-profiles/norns/cm3plus-norns-260102.json}
OUT=${OUT:-/out}
cd /opt/emulator
mkdir -p "$OUT"
{ git rev-parse HEAD; nproc; lscpu; cat /proc/loadavg; uname -a; } > "$OUT/host.txt" 2>&1
set -e
python3 scripts/build_performance_profile_runtime.py --output /tmp/profile-runtime > "$OUT/profile-runtime-build.log" 2>&1
python3 scripts/calibration/native_probe_run.py --output "$OUT/probe-default" --repeats 3
python3 scripts/calibration/native_probe_run.py --output "$OUT/probe-profiled" --repeats 3 \
  --experimental-install /tmp/profile-runtime/installation.json --performance-profile "$PROFILE"
set +e
python3 scripts/calibration/profile_check.py --profile "$PROFILE" --probe-run "$OUT/probe-default" --json "$OUT/verdict-default.json"
DEFAULT=$?
python3 scripts/calibration/profile_check.py --profile "$PROFILE" --probe-run "$OUT/probe-profiled" --json "$OUT/verdict-profiled.json"
PROFILED=$?
echo "default_check_exit=$DEFAULT profiled_check_exit=$PROFILED" | tee "$OUT/summary.txt"
test "$DEFAULT" -ne 0 && test "$PROFILED" -eq 0
