#!/bin/sh
# Private mount/network namespace only. Hides every installed application fixture.
set -eu
cd /mnt/c/Users/andy/Documents/ChatGPT/monome-emulator
mount --make-rprivate /
mount -t tmpfs -o size=1m,mode=0755 tmpfs "$PWD/upstream"
mount -t tmpfs -o size=1m,mode=0755 tmpfs "$PWD/.runtime/fixtures"
ip link set lo up
test -z "$(ls -A upstream)"
test -z "$(ls -A .runtime/fixtures)"
ip route show > artifacts/c02/isolated-routes.txt
runuser -u andy -- python3 dev/emu run fixtures/scenarios/native-probe-a.json > artifacts/c02/isolated-probe-a.json
runuser -u andy -- python3 dev/emu run fixtures/scenarios/native-probe-b.json > artifacts/c02/isolated-probe-b.json
