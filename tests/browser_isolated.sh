#!/bin/sh
# Called as root under a private mount namespace; networking remains available
# for the Windows browser to reach WSL's loopback server.
set -eu
case "$1" in probe-a|probe-b) ;; *) exit 2;; esac
cd /mnt/c/Users/andy/Documents/ChatGPT/monome-emulator
mount --make-rprivate /
mount -t tmpfs -o size=1m,mode=0755 tmpfs "$PWD/upstream"
mount -t tmpfs -o size=1m,mode=0755 tmpfs "$PWD/.runtime/fixtures"
test -z "$(ls -A upstream)"
test -z "$(ls -A .runtime/fixtures)"
runuser -u andy -- python3 dev/emu start --script "fixtures/probes/$1/$1.lua" --code-root fixtures/probes
