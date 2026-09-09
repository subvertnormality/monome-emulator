"""Verify browser-produced native audio and exact owned-process cleanup."""
import argparse,json,os,time
from pathlib import Path
from desktop_assertions import signal
from audio_feasibility import silence,ROOT,write_json

p=argparse.ArgumentParser();p.add_argument('report',type=Path);a=p.parse_args()
r=json.loads(a.report.read_text())
r['passed']=False
try:
    assert r.get('browser_passed') and not r['cleanup_errors'],r.get('error')
    r['audio_signal']=signal(Path(r['tone']['output']),440)
    r['audio_silence']=[silence(Path(r['silence']['output']),channel) for channel in (0,1)]
    for sid in r['sessions']:
        directory=ROOT/'.runtime/sessions'/sid
        deadline=time.monotonic()+5
        while not (directory/'stopped.json').exists() and time.monotonic()<deadline:time.sleep(.05)
        assert (directory/'stopped.json').exists(),sid
        rows=json.loads((directory/'cleanup.json').read_text())
        assert len(rows)==4 and {row['service'] for row in rows}=={'matron','crone','jack','sclang'},rows
        for row in rows:
            assert row['returncode'] in ((0,-15) if row['service']=='sclang' else (0,)),row
        maiden=json.loads((directory/'maiden-cleanup.json').read_text());assert maiden['returncode'] in (0,-15),maiden
        for row in rows+[maiden]:
            try:os.kill(row['pid'],0)
            except ProcessLookupError:pass
            else:raise AssertionError('Owned process survived: '+str(row))
    r['checks']+=['actual-stereo-tone-continuity-and-silence','all-owned-native-and-maiden-processes-reaped']
    r['passed']=True
    r.pop('verification_error',None)
except Exception as error:r['verification_error']=repr(error);raise
finally:write_json(a.report,r)
print(json.dumps(dict(passed=r['passed'],checks=r['checks'])),flush=True)
