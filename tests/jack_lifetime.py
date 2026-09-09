"""Compile actual pinned matron boundary; baseline must fail and candidate pass."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'scripts'))
from jack_lifetime_patch import apply

lock = json.loads((ROOT/'dependencies.lock.json').read_text())
revision = lock['dependencies']['norns']['commit']
cache = ROOT/'.runtime/deps/norns'
out = ROOT/'artifacts/docker/jack-lifetime'
out.mkdir(exist_ok=False)
with tempfile.TemporaryDirectory() as temp:
    source = Path(temp)
    native = source/'matron/src'
    native.mkdir(parents=True)
    for name in ('jack_client.c', 'jack_client.h'):
        (native/name).write_bytes(subprocess.check_output(['git', '-C', str(cache), 'show', revision+':matron/src/'+name]))
    results = []
    for variant in ('baseline', 'candidate'):
        if variant == 'candidate':
            patch = apply(source)
            assert patch == (ROOT/'patches/norns/experimental-jack-lifetime.patch').read_text()
        binary = source/variant
        wrapped = ['pthread_mutex_lock', 'jack_client_open', 'jack_activate', 'jack_set_xrun_callback',
                   'jack_get_sample_rate', 'jack_frame_time', 'jack_cpu_load', 'jack_client_close']
        subprocess.run(['gcc', '-std=gnu11', '-pthread', '-I'+str(native), str(native/'jack_client.c'),
                        str(ROOT/'tests/jack_lifetime.c'), '-o', str(binary), '-ljack'] +
                       ['-Wl,--wrap='+name for name in wrapped], check=True)
        run = subprocess.run([str(binary)], capture_output=True, text=True, timeout=10)
        (out/(variant+'.log')).write_text(run.stdout+run.stderr)
        results.append(dict(variant=variant, returncode=run.returncode))
        assert run.returncode == (-6 if variant == 'baseline' else 0), results
    (out/'report.json').write_text(json.dumps(dict(passed=True, norns_revision=revision,
        harness_sha256=hashlib.sha256((ROOT/'tests/jack_lifetime.c').read_bytes()).hexdigest(), results=results), indent=2)+'\n')
print(out/'report.json')
