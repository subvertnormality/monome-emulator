"""Verify the browser test's actual native process exits; never infer from HTTP."""
import argparse,json,os,time
from pathlib import Path
from audio_feasibility import ROOT,write_json
p=argparse.ArgumentParser();p.add_argument('report',type=Path);p.add_argument('--expected-browser-error');a=p.parse_args()
r=json.loads(a.report.read_text());browser_passed=r['passed'];r['passed']=False
try:
    if a.expected_browser_error:
        assert not browser_passed and a.expected_browser_error in json.dumps(r),r.get('error')
    else:assert browser_passed,r.get('error')
    directory=ROOT/'.runtime/sessions'/r['session_id']
    deadline=time.monotonic()+5
    while not (directory/'stopped.json').exists() and time.monotonic()<deadline:time.sleep(.05)
    assert (directory/'stopped.json').exists()
    rows=json.loads((directory/'cleanup.json').read_text())
    assert len(rows)==4 and {row['service'] for row in rows}=={'matron','crone','sclang','jack'},rows
    for row in rows:
        assert row['returncode'] in ((0,-15) if row['service']=='sclang' else (0,)),row
        try:os.kill(row['pid'],0)
        except ProcessLookupError:pass
        else:raise AssertionError('Owned process remains: '+str(row))
    r['native_cleanup']=rows;r['native_cleanup_verified']=True;r['passed']=browser_passed
except Exception as error:r['cleanup_verification_error']=repr(error);raise
finally:write_json(a.report,r)
print('PASS native process cleanup',flush=True)
