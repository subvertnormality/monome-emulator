#!/bin/bash
# Cross-host profile check inside the emulator image:
#   docker run --rm --user root --shm-size 256m -v "$PWD/out:/out" [-v <app>:/app:ro] \
#     --entrypoint bash <image> scripts/calibration/ci_profile_check.sh [profile.json]
# 1. Builds the opt-in profile runtime.
# 2. Runs the generic probe unprofiled and profiled (3 fresh sessions each) and
#    applies the fail-closed profile check. The unprofiled verdict is expected
#    to fail and shows the check detects a runtime that does not model the device.
# 3. When an application checkout is mounted at /app with APP_CASES set, runs
#    its opt-in calibration lane (APP_LANE, relative to /app) under the profile.
#    APP_ONLY=1 skips step 2 (the application lane is a separate, non-gating job).
#    The application lane records musical pass/fail; it fails only on harness errors.
set -u
PROFILE=${1:-profiles/norns/cm3plus-norns-260102.json}
OUT=${OUT:-/out}
cd /opt/emulator
mkdir -p "$OUT"
{ git rev-parse HEAD; nproc; lscpu; free -b; cat /proc/loadavg; uname -a; } > "$OUT/host.txt" 2>&1
if ! python3 scripts/build_performance_profile_runtime.py --output /tmp/profile-runtime > "$OUT/profile-runtime-build.log" 2>&1; then
  echo "profile runtime build failed" | tee "$OUT/summary.txt"; exit 1
fi
DEFAULT=skipped
PROFILED=skipped
if [ -z "${APP_ONLY:-}" ]; then
  python3 scripts/calibration/native_probe_run.py --output "$OUT/probe-default" --repeats 3
  python3 scripts/calibration/native_probe_run.py --output "$OUT/probe-profiled" --repeats 3 \
    --experimental-install /tmp/profile-runtime/installation.json --performance-profile "$PROFILE"
  python3 scripts/calibration/profile_check.py --profile "$PROFILE" --probe-run "$OUT/probe-default" --json "$OUT/verdict-default.json"
  DEFAULT=$?
  python3 scripts/calibration/profile_check.py --profile "$PROFILE" --probe-run "$OUT/probe-profiled" --json "$OUT/verdict-profiled.json"
  PROFILED=$?
fi
APP=skipped
if [ -d /app ] && [ -n "${APP_CASES:-}" ]; then
  APP=0
  git config --global --add safe.directory '*'
  PARAMS=$(python3 -c "import json,sys;print(json.dumps(json.load(open(sys.argv[1]))['runtime']['cost_parameters']))" "$PROFILE")
  for CASE in $APP_CASES; do
    ID=$(echo "$CASE" | tr 'A-Z' 'a-z' | tr -d '-')
    (cd /app && MONOME_EMULATOR=/opt/emulator python3 "$APP_LANE" --case "$CASE" --output "$OUT/app-profiled-$ID" --windows 4 \
       --experimental-install /tmp/profile-runtime/installation.json --cost-parameters "$PARAMS") > "$OUT/app-profiled-$ID.log" 2>&1 || APP=1
  done
fi
echo "default_check_exit=$DEFAULT profiled_check_exit=$PROFILED application_lane=$APP" | tee "$OUT/summary.txt"
if [ -n "${APP_ONLY:-}" ]; then
  [ "$APP" = 0 ]
else
  test "$DEFAULT" != 0 && test "$PROFILED" = 0 && [ "$APP" != 1 ]
fi
