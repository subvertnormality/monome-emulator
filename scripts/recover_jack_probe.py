"""One-time recovery of a proven stale C02 JACK registration using JACK itself."""
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from automation.protocol import ROOT,read_json,write_json
prefix=sys.argv[1] if len(sys.argv)>1 else 'afea5d5cc314495a'
assert len(prefix)>=16 and all(c in '0123456789abcdef' for c in prefix)
# Resolve the exact locally recorded identity rather than guessing a user server.
matches=list((ROOT/'.runtime/sessions').glob(prefix+'*'))
assert len(matches)==1
config=read_json(matches[0]/'native-config.json')
name=config['jack_server']
assert name=='emu-'+matches[0].name[:16]
for p in Path('/proc').iterdir():
    if not p.name.isdigit(): continue
    try: command=(p/'cmdline').read_bytes()
    except OSError: continue
    assert name.encode() not in command,('still active',p)
log=ROOT/'artifacts/c02/jack-recovery.log'
with open(log,'w') as stream:
    proc=subprocess.Popen(['jackd','--name',name,'--no-realtime','-d','dummy','-r','48000','-p','128'],
        stdout=stream,stderr=subprocess.STDOUT,start_new_session=True)
    time.sleep(1)
    assert proc.poll() is None,log.read_text()
    os.killpg(proc.pid,signal.SIGTERM)
    result=proc.wait(timeout=5)
write_json(ROOT/'artifacts/c02/jack-recovery.json',dict(server=name,returncode=result,log=str(log)))
assert result==0
