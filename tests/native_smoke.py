"""C02 native loader/device smoke via the same session API as all clients."""
import json
from pathlib import Path
import sys
import time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from automation import session
from automation.protocol import ROOT,uid,write_json

def smoke(info):
    sid=info['session_id']
    def action(sequence,body):
        return session.request(sid,'/action',dict(schema_version=1,session_id=sid,action_id=uid(),sequence=sequence,action=body))
    try:
        initial=session.request(sid,'/snapshot')
        assert initial['fidelity']=='native-norns' and initial['state']['ready']
        assert initial['state']['script']=='probe-b'
        initial_frame=initial['state']['frame']['sha256']
        action(1,dict(type='key',n=3,state=1))
        action(2,dict(type='key',n=3,state=0))
        action(3,dict(type='grid',x=16,y=8,state=1))
        action(4,dict(type='grid',x=16,y=8,state=0))
        end=time.monotonic()+3
        while True:
            observed=session.request(sid,'/snapshot')
            if any(m['bytes']==[0x82,67,0] for m in observed['state']['midi']): break
            if time.monotonic()>end: raise AssertionError('Native clock note-off missing')
            time.sleep(0.02)
        assert any(m['bytes']==[0x92,67,80] for m in observed['state']['midi'])
        assert observed['state']['grid'][-1]==0
        assert not observed['state']['held']
        assert observed['state']['frame']['sha256']!=initial_frame
        assert observed['state']['diagnostics']['params']>0
        write_json(ROOT/'artifacts/c02-native-smoke.json',dict(passed=True,initial=initial,observed=observed))
        print('Native generic load/include, keys, grid, note bytes, clock note-off and frame change passed')
    finally:
        session.stop(sid)

if __name__=='__main__':
    if len(sys.argv)>1: info=json.loads(Path(sys.argv[1]).read_text())
    else: info=session.start('native',ROOT/'fixtures/probes/probe-b/probe-b.lua',ROOT/'fixtures/probes')
    smoke(info)
