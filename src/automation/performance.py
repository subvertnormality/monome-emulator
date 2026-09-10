"""Resource and musical-performance measurements for native emulator runs.

The functions in this module never claim that a constrained x86 host is a
physical norns.  They provide comparable measurements and explicit gates for
the norns-class proxy described in docs/delivery/PERFORMANCE.md.
"""
import hashlib
import os
import platform
import secrets
import threading
import time
from pathlib import Path

from .protocol import ContractError


MIB = 1024 * 1024
MEMORY_LIMIT_BYTES = 768 * MIB
RSS_SLOPE_LIMIT_BYTES_PER_MINUTE = MIB


def _require(condition, message):
    if not condition:
        raise ContractError('performance_evidence', message)


def nearest_rank(values, percent):
    """Return a nearest-rank percentile without interpolation."""
    _require(isinstance(values, list) and values, 'Metric population is empty')
    _require(type(percent) is int and 1 <= percent <= 100,
             'Percentile must be an integer from 1 to 100')
    _require(all(type(value) is int and value >= 0 for value in values),
             'Metric population must contain nonnegative integer values')
    ordered = sorted(values)
    rank = (percent * len(ordered) + 99) // 100
    return ordered[rank - 1]


def _rss_slope(samples, window_ns=300_000_000_000):
    """Least-squares RSS slope over the final window, in bytes per minute."""
    finish = samples[-1]['monotonic_ns']
    if finish - samples[0]['monotonic_ns'] < window_ns:
        return None
    selected = [row for row in samples
                if row['monotonic_ns'] >= finish - window_ns]
    if len(selected) < 2 or selected[-1]['monotonic_ns'] == selected[0]['monotonic_ns']:
        return None
    origin = selected[0]['monotonic_ns']
    xs = [(row['monotonic_ns'] - origin) / 60_000_000_000 for row in selected]
    ys = [row['rss_bytes'] for row in selected]
    mean_x = sum(xs) / len(xs)
    mean_y = sum(ys) / len(ys)
    denominator = sum((value - mean_x) ** 2 for value in xs)
    if denominator == 0:
        return None
    return (sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys)) /
            denominator)


def performance_metrics(samples, timing_errors_ns, service_times_ns,
                        musical_events, shortest_deadline_ns,
                        quiet_queue_depth=0, overload_end_ns=None,
                        one_bar_ns=None):
    """Summarize one run and evaluate resource, timing and recovery gates."""
    _require(isinstance(samples, list) and len(samples) >= 2,
             'At least two resource samples are required')
    previous = -1
    required = ('monotonic_ns', 'cpu_ns', 'rss_bytes', 'queue_depth')
    for row in samples:
        _require(isinstance(row, dict) and all(field in row for field in required),
                 'Resource sample is missing required fields')
        _require(all(type(row[field]) is int and row[field] >= 0 for field in required),
                 'Resource counters must be nonnegative integer values')
        _require(row['monotonic_ns'] > previous,
                 'Resource sample timestamps must be strictly increasing')
        previous = row['monotonic_ns']
    _require(samples[-1]['cpu_ns'] >= samples[0]['cpu_ns'],
             'Aggregate CPU counter moved backwards')
    _require(type(musical_events) is int and musical_events > 0,
             'Musical event count must be positive')
    _require(type(shortest_deadline_ns) is int and shortest_deadline_ns > 0,
             'Shortest musical deadline must be positive')
    _require(isinstance(timing_errors_ns, list) and timing_errors_ns and
             all(type(value) is int for value in timing_errors_ns),
             'Timing errors must be a nonempty integer population')
    _require(isinstance(service_times_ns, list) and service_times_ns and
             all(type(value) is int and value >= 0 for value in service_times_ns),
             'Service times must be a nonempty nonnegative integer population')
    _require(type(quiet_queue_depth) is int and quiet_queue_depth >= 0,
             'Quiet queue depth must be nonnegative')

    absolute_errors = [abs(value) for value in timing_errors_ns]
    timing = {name: nearest_rank(absolute_errors, percentile)
              for name, percentile in (('p50_ns', 50), ('p95_ns', 95),
                                       ('p99_ns', 99), ('maximum_ns', 100))}
    service = {name: nearest_rank(service_times_ns, percentile)
               for name, percentile in (('p50_ns', 50), ('p95_ns', 95),
                                        ('p99_ns', 99), ('maximum_ns', 100))}
    service['p99_deadline_fraction'] = service['p99_ns'] / shortest_deadline_ns
    service['maximum_deadline_fraction'] = service['maximum_ns'] / shortest_deadline_ns
    cpu_delta = samples[-1]['cpu_ns'] - samples[0]['cpu_ns']
    slope = _rss_slope(samples)

    recovered_ns = None
    recovery_passed = None
    if overload_end_ns is not None or one_bar_ns is not None:
        _require(type(overload_end_ns) is int and overload_end_ns >= 0 and
                 type(one_bar_ns) is int and one_bar_ns > 0,
                 'Overload recovery requires valid end and one-bar timestamps')
        for row in samples:
            if row['monotonic_ns'] >= overload_end_ns and row['queue_depth'] <= quiet_queue_depth:
                recovered_ns = row['monotonic_ns'] - overload_end_ns
                break
        recovery_passed = recovered_ns is not None and recovered_ns <= one_bar_ns

    peak_rss = max((row.get('peak_rss_bytes')
                    if row.get('peak_rss_bytes') is not None
                    else row['rss_bytes']) for row in samples)
    gates = dict(
        event_timing=(timing['p99_ns'] <= 10_000_000 and
                      timing['maximum_ns'] <= 50_000_000 and
                      abs(timing_errors_ns[-1]) <= 20_000_000),
        memory_peak=peak_rss <= MEMORY_LIMIT_BYTES,
        memory_slope=(None if slope is None else
                      slope <= RSS_SLOPE_LIMIT_BYTES_PER_MINUTE),
        sustained_service=service['p99_deadline_fraction'] <= 0.5,
        hard_service=service['maximum_deadline_fraction'] <= 1.0,
        queue_recovery=recovery_passed,
    )
    applicable = [value for value in gates.values() if value is not None]
    return dict(
        sample_count=len(samples), musical_events=musical_events,
        timing=timing,
        final_phase_error_ns=timing_errors_ns[-1],
        service=service,
        resources=dict(cpu_delta_ns=cpu_delta,
                       cpu_ns_per_musical_event=cpu_delta / musical_events,
                       peak_rss_bytes=peak_rss,
                       final_window_rss_slope_bytes_per_minute=slope,
                       queue_high_water=max(row['queue_depth'] for row in samples),
                       queue_recovery_ns=recovered_ns),
        gates=gates, passed=all(applicable))


def compare_performance(baseline, candidate):
    """Apply same-host candidate budgets from PERFORMANCE.md."""
    for value, label in ((baseline, 'baseline'), (candidate, 'candidate')):
        _require(isinstance(value, dict) and 'timing' in value and 'resources' in value,
                 'Invalid ' + label + ' performance report')
    base_p99 = baseline['timing']['p99_ns']
    base_cpu = baseline['resources']['cpu_ns_per_musical_event']
    candidate_p99 = candidate['timing']['p99_ns']
    candidate_cpu = candidate['resources']['cpu_ns_per_musical_event']
    timing_limit = base_p99 * 1.10
    cpu_limit = base_cpu * 1.15
    gates = dict(p99_timing=candidate_p99 <= timing_limit,
                 cpu_per_event=candidate_cpu <= cpu_limit)
    return dict(gates=gates, passed=all(gates.values()),
                baseline=dict(p99_ns=base_p99, cpu_ns_per_musical_event=base_cpu),
                candidate=dict(p99_ns=candidate_p99, cpu_ns_per_musical_event=candidate_cpu),
                limits=dict(p99_ns=timing_limit, cpu_ns_per_musical_event=cpu_limit))


def process_stat(text):
    """Parse stable identity and counters from /proc/<pid>/stat."""
    end = text.rfind(')')
    _require(end >= 0, 'Malformed process stat')
    fields = text[end + 2:].split()
    _require(len(fields) >= 22, 'Truncated process stat')
    return dict(state=fields[0], parent=int(fields[1]),
                user_ticks=int(fields[11]), system_ticks=int(fields[12]),
                threads=int(fields[17]), start_ticks=int(fields[19]),
                rss_pages=int(fields[21]))


class ProcessTreeSampler:
    """Aggregate CPU, RSS and context switches for one owned process tree."""
    def __init__(self, root_pid, proc=Path('/proc'), clock_ticks=None,
                 page_size=None):
        self.root_pid = root_pid
        self.proc = Path(proc)
        self.clock_ticks = clock_ticks or os.sysconf('SC_CLK_TCK')
        self.page_size = page_size or os.sysconf('SC_PAGE_SIZE')
        self.known = {}

    def _status_switches(self, path):
        values = {'voluntary_ctxt_switches': 0, 'nonvoluntary_ctxt_switches': 0}
        for line in path.read_text().splitlines():
            key, _, value = line.partition(':')
            if key in values:
                values[key] = int(value.strip())
        return values

    def sample(self, monotonic_ns, queue_depth=0):
        _require(type(monotonic_ns) is int and monotonic_ns >= 0,
                 'Sample timestamp must be a nonnegative integer')
        processes = {}
        for path in self.proc.iterdir():
            if not path.name.isdigit():
                continue
            try:
                processes[int(path.name)] = process_stat((path / 'stat').read_text())
            except (FileNotFoundError, ProcessLookupError, PermissionError):
                continue
        selected = set()
        for pid in processes:
            ancestor = pid
            seen = set()
            while ancestor in processes and ancestor not in seen:
                if ancestor == self.root_pid:
                    selected.add(pid)
                    break
                seen.add(ancestor)
                ancestor = processes[ancestor]['parent']
        rss = voluntary = involuntary = active_threads = 0
        for pid in selected:
            info = processes[pid]
            identity = (pid, info['start_ticks'])
            cpu_ticks = info['user_ticks'] + info['system_ticks']
            try:
                switches = self._status_switches(self.proc / str(pid) / 'status')
            except (FileNotFoundError, ProcessLookupError, PermissionError):
                switches = {'voluntary_ctxt_switches': 0,
                            'nonvoluntary_ctxt_switches': 0}
            prior = self.known.get(identity, dict(cpu_ticks=0, voluntary=0,
                                                  involuntary=0))
            self.known[identity] = dict(
                cpu_ticks=max(cpu_ticks, prior['cpu_ticks']),
                voluntary=max(switches['voluntary_ctxt_switches'],
                              prior['voluntary']),
                involuntary=max(switches['nonvoluntary_ctxt_switches'],
                                prior['involuntary']))
            rss += max(info['rss_pages'], 0) * self.page_size
            active_threads += info['threads']
            voluntary += switches['voluntary_ctxt_switches']
            involuntary += switches['nonvoluntary_ctxt_switches']
        cpu_ticks = sum(value['cpu_ticks'] for value in self.known.values())
        voluntary = sum(value['voluntary'] for value in self.known.values())
        involuntary = sum(value['involuntary'] for value in self.known.values())
        return dict(monotonic_ns=monotonic_ns,
                    cpu_ns=cpu_ticks * 1_000_000_000 // self.clock_ticks,
                    rss_bytes=rss, queue_depth=queue_depth,
                    process_count=len(selected), thread_count=active_threads,
                    voluntary_context_switches=voluntary,
                    involuntary_context_switches=involuntary)


class CgroupStatsSampler:
    """Read authoritative aggregate counters and limits inside a container."""
    def __init__(self, root=Path('/sys/fs/cgroup')):
        self.root = Path(root)
        if (self.root / 'cpu.stat').is_file() and (self.root / 'memory.current').is_file():
            self.version = 2
        elif ((self.root / 'cpuacct/cpuacct.usage').is_file() and
              (self.root / 'memory/memory.usage_in_bytes').is_file()):
            self.version = 1
        else:
            raise ContractError('cgroup_counters_missing',
                                'Aggregate CPU and memory cgroup counters are unavailable')

    def _integer(self, path):
        try:
            return int(path.read_text().strip())
        except (OSError, ValueError) as error:
            raise ContractError('cgroup_counter', str(error)) from error

    def sample(self, monotonic_ns, queue_depth=0):
        _require(type(monotonic_ns) is int and monotonic_ns >= 0 and
                 type(queue_depth) is int and queue_depth >= 0,
                 'Cgroup sample timestamp and queue depth must be nonnegative integers')
        if self.version == 2:
            cpu = {}
            try:
                for line in (self.root / 'cpu.stat').read_text().splitlines():
                    key, value = line.split()
                    cpu[key] = int(value)
            except (OSError, ValueError) as error:
                raise ContractError('cgroup_counter', str(error)) from error
            _require('usage_usec' in cpu, 'cgroup v2 CPU usage is missing')
            peak_path = self.root / 'memory.peak'
            peak = self._integer(peak_path) if peak_path.is_file() else None
            return dict(monotonic_ns=monotonic_ns,
                        cpu_ns=cpu['usage_usec'] * 1000,
                        rss_bytes=self._integer(self.root / 'memory.current'),
                        peak_rss_bytes=peak, queue_depth=queue_depth,
                        throttled_periods=cpu.get('nr_throttled'),
                        throttled_ns=(cpu.get('throttled_usec') * 1000
                                      if 'throttled_usec' in cpu else None))
        cpu_stat = {}
        try:
            for line in (self.root / 'cpu/cpu.stat').read_text().splitlines():
                key, value = line.split()
                cpu_stat[key] = int(value)
        except (OSError, ValueError) as error:
            raise ContractError('cgroup_counter', str(error)) from error
        return dict(monotonic_ns=monotonic_ns,
                    cpu_ns=self._integer(self.root / 'cpuacct/cpuacct.usage'),
                    rss_bytes=self._integer(self.root / 'memory/memory.usage_in_bytes'),
                    peak_rss_bytes=self._integer(self.root / 'memory/memory.max_usage_in_bytes'),
                    queue_depth=queue_depth,
                    throttled_periods=cpu_stat.get('nr_throttled'),
                    throttled_ns=(cpu_stat.get('throttled_time')
                                  if 'throttled_time' in cpu_stat else None))

    def limits(self):
        if self.version == 2:
            cpu = (self.root / 'cpu.max').read_text().split()
            swap_path = self.root / 'memory.swap.max'
            swap = swap_path.read_text().strip() if swap_path.is_file() else None
            return dict(cgroup_version=2,
                        cpu_quota_us=None if cpu[0] == 'max' else int(cpu[0]),
                        cpu_period_us=int(cpu[1]),
                        memory_limit_bytes=None if (self.root / 'memory.max').read_text().strip() == 'max'
                        else self._integer(self.root / 'memory.max'),
                        memory_swap_limit_bytes=(None if swap in (None, 'max')
                                                 else int(swap)),
                        cpuset_cpus=(self.root / 'cpuset.cpus.effective').read_text().strip())
        return dict(cgroup_version=1,
                    cpu_quota_us=self._integer(self.root / 'cpu/cpu.cfs_quota_us'),
                    cpu_period_us=self._integer(self.root / 'cpu/cpu.cfs_period_us'),
                    memory_limit_bytes=self._integer(self.root / 'memory/memory.limit_in_bytes'),
                    memory_and_swap_limit_bytes=self._integer(
                        self.root / 'memory/memory.memsw.limit_in_bytes'),
                    cpuset_cpus=(self.root / 'cpuset/cpuset.cpus').read_text().strip())


class PerformanceRecorder:
    """Bounded, paginated background capture of aggregate resource counters."""
    def __init__(self, sampler, period_ms, maximum_seconds, queue_depth=None,
                 autostart=True):
        _require(type(period_ms) is int and 10 <= period_ms <= 1000,
                 'Performance sample period must be from 10 to 1000 ms')
        _require(type(maximum_seconds) is int and 1 <= maximum_seconds <= 600,
                 'Performance recording must be from 1 to 600 seconds')
        self.id = secrets.token_hex(16)
        self.sampler = sampler
        self.period_ms = period_ms
        self.maximum_seconds = maximum_seconds
        self.maximum_samples = maximum_seconds * 1000 // period_ms + 2
        self.queue_depth = queue_depth or (lambda: 0)
        self.samples = []
        self.lock = threading.Lock()
        self.stopping = threading.Event()
        self.state = 'running'
        self.error = None
        self.started_ns = time.monotonic_ns()
        self.finished_ns = None
        self.thread = None
        if autostart:
            if not self.record_once():
                raise ContractError(self.error['code'], self.error['message'])
            self.thread = threading.Thread(target=self._run, daemon=True)
            self.thread.start()

    def record_once(self, monotonic_ns=None):
        with self.lock:
            if self.state != 'running':
                return False
            if len(self.samples) >= self.maximum_samples:
                self.state = 'complete'
                self.finished_ns = time.monotonic_ns()
                self.stopping.set()
                return False
        try:
            value = self.sampler.sample(
                monotonic_ns if monotonic_ns is not None else time.monotonic_ns(),
                self.queue_depth())
            _require(isinstance(value, dict), 'Performance sampler returned no record')
        except Exception as error:
            failure = (error if isinstance(error, ContractError) else
                       ContractError('performance_sample', str(error)))
            with self.lock:
                self.error = failure.as_dict()
                self.state = 'failed'
                self.finished_ns = time.monotonic_ns()
                self.stopping.set()
            return False
        with self.lock:
            if self.state != 'running':
                return False
            sequence = len(self.samples) + 1
            self.samples.append(dict(sequence=sequence, **value))
            return True

    def _run(self):
        deadline = time.monotonic() + self.maximum_seconds
        while self.state == 'running':
            remaining = min(self.period_ms / 1000,
                            max(0, deadline - time.monotonic()))
            if self.stopping.wait(remaining):
                break
            if time.monotonic() >= deadline:
                with self.lock:
                    if self.state == 'running':
                        self.state = 'complete'
                        self.finished_ns = time.monotonic_ns()
                break
            self.record_once()

    def status(self):
        with self.lock:
            return dict(recording_id=self.id, status=self.state,
                        period_ms=self.period_ms,
                        maximum_seconds=self.maximum_seconds,
                        sample_count=len(self.samples), cursor=len(self.samples),
                        started_ns=self.started_ns, finished_ns=self.finished_ns,
                        error=self.error)

    def read(self, after, limit=1000):
        _require(type(after) is int and after >= 0,
                 'Performance cursor must be a nonnegative integer')
        _require(type(limit) is int and 1 <= limit <= 1000,
                 'Performance page limit must be from 1 to 1000')
        with self.lock:
            _require(after <= len(self.samples),
                     'Performance cursor is beyond recorded samples')
            rows = self.samples[after:after + limit]
            cursor = after + len(rows)
            return dict(recording_id=self.id, samples=list(rows), cursor=cursor,
                        has_more=cursor < len(self.samples), status=self.state,
                        error=self.error)

    def stop(self):
        with self.lock:
            if self.state == 'running':
                self.state = 'stopped'
                self.finished_ns = time.monotonic_ns()
        self.stopping.set()
        if self.thread and self.thread is not threading.current_thread():
            self.thread.join(timeout=2)
            if self.thread.is_alive():
                raise ContractError('performance_stop',
                                    'Performance recorder did not stop within two seconds')
        return self.status()


def cgroup_capability(root=Path('/sys/fs/cgroup'), proc_cgroup=None):
    """Report whether a delegated cgroup v2 can enforce the required envelope."""
    root = Path(root)
    if proc_cgroup is None:
        try:
            proc_cgroup = Path('/proc/self/cgroup').read_text()
        except OSError as error:
            return dict(available=False, code='cgroup_unavailable', reason=str(error))
    unified = [line.split(':', 2)[2] for line in proc_cgroup.splitlines()
               if line.startswith('0::')]
    if len(unified) != 1:
        return dict(available=False, code='cgroup_v2_required',
                    reason='A single unified cgroup v2 membership is required')
    current = root / unified[0].lstrip('/')
    try:
        controllers = set((current / 'cgroup.controllers').read_text().split())
    except OSError as error:
        return dict(available=False, code='cgroup_unavailable', reason=str(error),
                    path=str(current))
    missing = sorted({'cpu', 'memory', 'cpuset'} - controllers)
    if missing:
        return dict(available=False, code='cgroup_controllers_missing',
                    reason='Required controllers are not delegated: ' + ', '.join(missing),
                    path=str(current), controllers=sorted(controllers))
    if not os.access(str(current), os.W_OK):
        return dict(available=False, code='cgroup_not_delegated',
                    reason='Current cgroup is not writable by this user',
                    path=str(current), controllers=sorted(controllers))
    return dict(available=True, code=None, reason=None, path=str(current),
                controllers=sorted(controllers))


def calibrate_cpu(iterations=250_000):
    """Run a versioned deterministic CPU calibration for same-profile comparison."""
    _require(type(iterations) is int and 10_000 <= iterations <= 10_000_000,
             'Calibration iterations must be from 10000 to 10000000')
    state = bytearray(hashlib.sha256(b'norns-class-proxy-calibration-v1').digest())
    wall_start = time.monotonic_ns()
    cpu_start = time.process_time_ns()
    for index in range(iterations):
        slot = index & 31
        state[slot] = (state[slot] * 33 + state[(slot - 7) & 31] + index) & 255
    cpu_ns = time.process_time_ns() - cpu_start
    wall_ns = time.monotonic_ns() - wall_start
    _require(cpu_ns > 0 and wall_ns > 0, 'Calibration clock did not advance')
    return dict(algorithm='python-byte-mix-v1', iterations=iterations,
                checksum=hashlib.sha256(state).hexdigest(), wall_ns=wall_ns,
                cpu_ns=cpu_ns,
                iterations_per_cpu_second=iterations * 1_000_000_000 / cpu_ns)


def performance_capabilities(calibration_iterations=250_000):
    """Describe this host and whether the mandatory constrained lane can run."""
    memory = {}
    try:
        for line in Path('/proc/meminfo').read_text().splitlines():
            key, _, value = line.partition(':')
            if key in ('MemTotal', 'MemAvailable'):
                memory[key] = int(value.split()[0]) * 1024
    except (OSError, ValueError, IndexError):
        pass
    affinity = None
    if hasattr(os, 'sched_getaffinity'):
        affinity = sorted(os.sched_getaffinity(0))
    return dict(schema_version=1, claim='norns-class-proxy-only',
                host=dict(platform=platform.platform(), machine=platform.machine(),
                          python=platform.python_version(), cpu_count=os.cpu_count(),
                          affinity=affinity, memory=memory),
                constrained=cgroup_capability(),
                calibration=calibrate_cpu(calibration_iterations))
