"""Record measured host and tool facts; absence is data, not success."""
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import time

ROOT = Path(__file__).resolve().parents[2]
def command(args):
    try:
        run = subprocess.run(args, capture_output=True, text=True, timeout=20)
        return dict(exit_code=run.returncode, stdout=run.stdout, stderr=run.stderr)
    except (OSError, subprocess.TimeoutExpired) as error:
        return dict(error=str(error))

report = dict(timestamp=time.time(), kernel=platform.uname()._asdict(),
              distro=Path('/etc/os-release').read_text(), cpu_count=os.cpu_count(),
              memory=Path('/proc/meminfo').read_text(), workspace=str(ROOT),
              disk=shutil.disk_usage(ROOT)._asdict(),
              devices={p:Path(p).exists() for p in ['/dev/snd', '/dev/snd/seq', '/dev/fb0', '/mnt/wslg']},
              tools={name:shutil.which(name) for name in ['gcc','g++','make','cmake','lua5.3','python3','node','npm','jackd','docker']},
              packages=command(['dpkg-query','-W','libasound2-dev','libudev-dev','libevdev-dev','libgpiod-dev','liblo-dev','libcairo2-dev','liblua5.3-dev','libnanomsg-dev','libavahi-compat-libdnssd-dev','libsndfile1-dev','libjack-jackd2-dev','libsdl2-dev','jackd2']))
(ROOT/'artifacts/c00/host.json').write_text(json.dumps(report, indent=2)+'\n')
print(json.dumps({k:report[k] for k in ['kernel','cpu_count','devices','tools']}))
