#!/bin/sh
# Run only under `unshare --mount --net --fork`; mounts cannot propagate outward.
set -eu
cd /mnt/c/Users/andy/Documents/ChatGPT/monome-emulator
mount --make-rprivate /
mount -t tmpfs -o size=1m,mode=0755 tmpfs "$PWD/upstream"
ip link set lo up
test -z "$(ls -A upstream)"
# No route to GitHub/app sources exists in this network namespace.
ip route show > artifacts/c00/isolated-routes.txt
runuser -u andy -- python3 probes/c00/boot.py
