#!/usr/bin/env python3
"""Read-only per-thread runtime sampler shared by the norns and emulator lanes.

    ssh we@<norns> python3 - --seconds 12 < scripts/calibration/thread_sampler.py > samples.jsonl
    docker exec -i <container> python3 - --seconds 12 < scripts/calibration/thread_sampler.py

Emits JSON lines: one ``identity`` row, then ``sample`` rows. Each sample pairs
CLOCK_MONOTONIC with CLOCK_REALTIME so wall-clock Lua timestamps (norns
``util.time`` uses gettimeofday) can be mapped to monotonic time and slewing is
visible. Per-thread CPU and run-queue wait come from ``/proc/<pid>/task/<tid>/
schedstat`` (nanoseconds). Nothing is written except stdout. Python 3.5+.
"""
import argparse, json, os, sys, time

RUNTIME = ('matron', 'crone', 'jackd', 'sclang', 'scsynth')


def read(path):
    try:
        with open(path) as handle:
            return handle.read()
    except (IOError, OSError):
        return None


def ns_now(clock):
    return int(time.clock_gettime(clock) * 1e9) if not hasattr(time, 'clock_gettime_ns') else time.clock_gettime_ns(clock)


def processes(names):
    found = {}
    for pid in os.listdir('/proc'):
        if pid.isdigit():
            comm = (read('/proc/%s/comm' % pid) or '').strip()
            if comm in names:
                found[int(pid)] = comm
    return found


def thread_rows(pid, comms, detail=False):
    """Compact per-thread row: [tid, cpu_ns, runqueue_wait_ns, timeslices]."""
    rows = []
    try:
        tids = os.listdir('/proc/%d/task' % pid)
    except OSError:
        return rows
    for tid in tids:
        base = '/proc/%d/task/%s/' % (pid, tid)
        sched = read(base + 'schedstat')
        if sched is None:
            continue
        run_ns, wait_ns, slices = (int(x) for x in sched.split()[:3])
        key = (pid, tid)
        if detail or key not in comms:
            stat = read(base + 'stat') or ''
            fields = stat[stat.rfind(')') + 2:].split()
            comms[key] = dict(comm=(read(base + 'comm') or '').strip(), policy=int(fields[38]) if len(fields) > 38 else None,
                              rt_priority=int(fields[37]) if len(fields) > 37 else None, nice=int(fields[16]) if len(fields) > 16 else None)
        rows.append([int(tid), run_ns, wait_ns, slices])
    return rows


def system_row():
    stat = read('/proc/stat') or ''
    cpus, extra = {}, {}
    for line in stat.splitlines():
        parts = line.split()
        if parts and parts[0].startswith('cpu'):
            cpus[parts[0]] = [int(x) for x in parts[1:]]
        elif parts and parts[0] in ('ctxt', 'intr', 'procs_running', 'procs_blocked'):
            extra[parts[0]] = int(parts[1])
    meminfo = {}
    for line in (read('/proc/meminfo') or '').splitlines():
        key, _, value = line.partition(':')
        if key in ('MemTotal', 'MemAvailable', 'SwapTotal', 'SwapFree', 'Dirty', 'Writeback'):
            meminfo[key] = int(value.split()[0]) * 1024
    vmstat = {}
    for line in (read('/proc/vmstat') or '').splitlines():
        key, value = line.split()
        if key in ('pswpin', 'pswpout', 'pgmajfault', 'pgfault'):
            vmstat[key] = int(value)
    disks = {}
    for line in (read('/proc/diskstats') or '').splitlines():
        parts = line.split()
        if len(parts) > 13 and (parts[2] == 'mmcblk0' or parts[2] in ('sda', 'nvme0n1', 'vda', 'sdb', 'sdc', 'sdd')):
            disks[parts[2]] = [int(x) for x in parts[3:14]]
    pressure = {}
    for kind in ('cpu', 'memory', 'io'):
        text = read('/proc/pressure/' + kind)
        if text is not None:
            pressure[kind] = text.strip().splitlines()
    thermal = read('/sys/class/thermal/thermal_zone0/temp')
    freqs = [read('/sys/devices/system/cpu/cpu%d/cpufreq/scaling_cur_freq' % n) for n in range(os.cpu_count() or 1)]
    return dict(cpu_jiffies=cpus, meminfo=meminfo, vmstat=vmstat, diskstats=disks, pressure=pressure,
                loadavg=(read('/proc/loadavg') or '').split()[:4],
                thermal_millicelsius=int(thermal) if thermal and thermal.strip().lstrip('-').isdigit() else None,
                cpu_freq_khz=[int(f) if f and f.strip().isdigit() else None for f in freqs], **extra)


def throttled():
    try:
        import subprocess
        raw = subprocess.check_output(['vcgencmd', 'get_throttled'], stderr=subprocess.DEVNULL).decode().strip()
        return int(raw.rsplit('=', 1)[1], 16)
    except Exception:
        return None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--seconds', type=float, required=True)
    parser.add_argument('--period', type=float, default=0.1)
    parser.add_argument('--names', default=','.join(RUNTIME))
    parser.add_argument('--system-every', type=int, default=10, help='system counters every N samples; 0 disables')
    args = parser.parse_args()
    if not 0.02 <= args.period <= 5 or not 0 < args.seconds <= 3600:
        parser.error('period must be 0.02..5 s and seconds 0..3600')
    names = set(args.names.split(','))
    procs = processes(names)
    print(json.dumps(dict(kind='identity', uname=list(os.uname()), boot_id=(read('/proc/sys/kernel/random/boot_id') or '').strip(),
                          clock_ticks=os.sysconf('SC_CLK_TCK'), page_size=os.sysconf('SC_PAGE_SIZE'), cpu_count=os.cpu_count(),
                          processes={str(pid): dict(comm=comm, cmdline=(read('/proc/%d/cmdline' % pid) or '').replace('\0', ' ').strip(),
                                                    start_ticks=int((read('/proc/%d/stat' % pid) or '').rsplit(')', 1)[-1].split()[19]))
                                     for pid, comm in procs.items()},
                          sampler_pid=os.getpid(), period_s=args.period, throttled_start=throttled(), system=system_row(),
                          thread_row_fields=['tid', 'cpu_ns', 'runqueue_wait_ns', 'timeslices'])), flush=True)
    comms = {}
    deadline = time.monotonic() + args.seconds
    ordinal = 0
    while True:
        started = ns_now(time.CLOCK_MONOTONIC)
        row = dict(kind='sample', ordinal=ordinal, monotonic_ns=started, realtime_ns=ns_now(time.CLOCK_REALTIME),
                   threads={str(pid): thread_rows(pid, comms) for pid in procs},
                   sampler=thread_rows(os.getpid(), comms))
        if args.system_every and ordinal % args.system_every == 0:
            row['system'] = system_row()
        row['sample_cost_ns'] = ns_now(time.CLOCK_MONOTONIC) - started
        print(json.dumps(row), flush=True)
        ordinal += 1
        if time.monotonic() >= deadline:
            break
        time.sleep(max(0.0, args.period - row['sample_cost_ns'] / 1e9))
    print(json.dumps(dict(kind='end', monotonic_ns=ns_now(time.CLOCK_MONOTONIC), realtime_ns=ns_now(time.CLOCK_REALTIME),
                          throttled_end=throttled(), samples=ordinal, system=system_row(),
                          thread_names={'%d/%s' % key: value for key, value in comms.items()})), flush=True)


if __name__ == '__main__':
    sys.exit(main())
