#!/bin/bash
# Read-only physical-norns identity and timing-configuration snapshot.
#
#   ssh we@<norns> bash -s < scripts/calibration/norns_identity.sh > identity.txt
#
# Writes nothing on the device: no sudo, no Lua evaluation, no git status or
# describe (both can refresh the index stat cache), no service changes. Sections are delimited so the
# host-side parser can keep missing tools as explicit UNAVAILABLE rows.
set -u
export LC_ALL=C GIT_OPTIONAL_LOCKS=0
section() { printf '\n=== %s\n' "$1"; }
run() { if command -v "$1" >/dev/null 2>&1; then "$@" 2>&1; else echo "UNAVAILABLE: $1"; fi; }
show() { for f in "$@"; do if [ -r "$f" ]; then printf -- '--- %s\n' "$f"; tr -d '\0' < "$f"; echo; else echo "UNREADABLE: $f"; fi; done; }

section clocks
printf 'monotonic_ns %s\nrealtime_ns %s\n' "$(python3 -c 'import time;print(time.monotonic_ns())')" "$(date +%s%N)"
section hardware
show /proc/device-tree/model /proc/cpuinfo /proc/meminfo
run vcgencmd version; run vcgencmd get_mem arm; run vcgencmd get_mem gpu
run vcgencmd measure_clock arm; run vcgencmd measure_temp; run vcgencmd measure_volts core
run vcgencmd get_throttled; run vcgencmd get_config int
for c in /sys/devices/system/cpu/cpu[0-9]*; do
  echo "$c online=$(cat $c/online 2>/dev/null || echo n/a) governor=$(cat $c/cpufreq/scaling_governor 2>/dev/null) cur=$(cat $c/cpufreq/scaling_cur_freq 2>/dev/null) min=$(cat $c/cpufreq/scaling_min_freq 2>/dev/null) max=$(cat $c/cpufreq/scaling_max_freq 2>/dev/null)"
done
show /sys/class/thermal/thermal_zone0/temp /sys/class/thermal/thermal_zone0/type
section os
run uname -a; show /etc/os-release /etc/debian_version /proc/cmdline /proc/version
show /sys/devices/system/clocksource/clocksource0/current_clocksource
show /proc/sys/kernel/sched_rt_runtime_us /proc/sys/kernel/sched_rt_period_us /proc/sys/vm/swappiness
run swapon --show; ls -d /proc/pressure/* 2>&1; show /proc/self/schedstat
run timedatectl show; run systemctl is-active systemd-timesyncd
section norns
show /home/we/version.txt
run git -C /home/we/norns rev-parse HEAD
# status/describe --dirty may refresh the index stat cache even without locks; hash tracked files instead.
run git -C /home/we/norns ls-files -s -- lua matron/src crone/src | sha256sum
for f in /home/we/norns/build/matron/matron /home/we/norns/build/crone/crone /home/we/norns/lua/core/clock.lua /home/we/norns/lua/core/midi.lua /home/we/norns/lua/core/grid.lua; do
  [ -e "$f" ] && { sha256sum "$f"; stat -c '%n %s %y' "$f"; } || echo "MISSING: $f"
done
run git -C /home/we/maiden rev-parse HEAD
section services
run systemctl list-units --type=service --all --no-legend
for u in norns-jack norns-matron norns-crone norns-sclang norns-maiden norns-watcher; do
  run systemctl show "$u" -p ActiveState -p ExecStart -p Nice -p CPUSchedulingPolicy -p CPUSchedulingPriority -p CPUAffinity -p ActiveEnterTimestamp
done
section processes
run ps -eLo pid,tid,cls,rtprio,ni,pri,psr,pcpu,rss,stat,etimes,comm,args --sort=-pcpu | head -80
for p in jackd matron crone sclang scsynth; do
  for pid in $(pgrep -x "$p"); do printf -- '--- %s %s: ' "$p" "$pid"; tr '\0' ' ' < /proc/$pid/cmdline; echo; ls /proc/$pid/task | while read t; do echo "task $t $(cat /proc/$pid/task/$t/comm) sched=$(cat /proc/$pid/task/$t/schedstat 2>/dev/null)"; done; done
done
section load
show /proc/loadavg /proc/stat /proc/interrupts /proc/softirqs /proc/vmstat
run top -b -n 1 | head -30
section network
run ip -brief addr; run iw dev; run rfkill list
section devices
run lsusb; run lsusb -t; show /proc/asound/cards; run amidi -l; run aconnect -l
ls -l /dev/ttyUSB* /dev/ttyACM* /dev/serial/by-id 2>&1
section storage
run df -h /home/we; grep -E ' / | /boot ' /proc/mounts; show /sys/block/mmcblk0/device/name /sys/block/mmcblk0/device/type /proc/diskstats
section mosaic
ls -la /home/we/dust/code 2>&1
if [ -d /home/we/dust/code/mosaic ]; then
  run git -C /home/we/dust/code/mosaic rev-parse HEAD
  (cd /home/we/dust/code/mosaic && find . -type f -not -path './.git/*' -print0 | sort -z | xargs -0 sha256sum) > /dev/stdout
fi
ls -la /home/we/.cache/mosaic-real-norns 2>&1
section logs
for u in norns-jack norns-matron norns-crone norns-sclang; do run journalctl -u "$u" -n 120 --no-pager; done
section end
printf 'monotonic_ns %s\n' "$(python3 -c 'import time;print(time.monotonic_ns())')"
