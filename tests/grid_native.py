"""C03 native grid conformance and Mosaic navigation; independent byte/LED tables."""
import json
from pathlib import Path
import shutil
import sys
import time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from automation import session
from automation.identity import source_identity
from automation.protocol import ROOT,ContractError,uid,write_json
import app_fixtures

class Client:
    def __init__(self,script=None,code=None,fixture=False):
        if fixture: self.info=session.start('native',**app_fixtures.launch_options('mosaic','base-midi'))
        else: self.info=session.start('native',script or ROOT/'fixtures/probes/grid-probe/grid-probe.lua',code or ROOT/'fixtures/probes')
        self.sid=self.info['session_id']; self.seq=0; self.trace=[]; self.observations=[]
    def snapshot(self):
        observation=session.request(self.sid,'/snapshot'); self.observations.append(observation); return observation
    def action(self,**action):
        request=dict(schema_version=1,session_id=self.sid,action_id=uid(),sequence=self.seq+1,action=action)
        ack=session.request(self.sid,'/action',request)
        self.seq+=1; self.trace.append(dict(request=request,ack=ack))
    def press(self,x,y,z): self.action(type='grid',x=x,y=y,state=z)
    def key(self,n): self.action(type='key',n=n,state=1); self.action(type='key',n=n,state=0)
    def wait(self,predicate,description):
        end=time.monotonic()+2
        while True:
            obs=self.snapshot()
            if predicate(obs): return obs
            if time.monotonic()>end: raise AssertionError(description)
            time.sleep(.02)
    def finish(self,name):
        session.stop(self.sid)
        directory=session.SESSIONS/self.sid
        cleanup=json.loads((directory/'cleanup.json').read_text())
        assert all(c['returncode']==0 for c in cleanup if c['service']!='sclang'),cleanup
        out=ROOT/'artifacts/c03'/name; out.mkdir(parents=True,exist_ok=True)
        write_json(out/'trace.json',self.trace); write_json(out/'observations.json',self.observations)
        for path in directory.iterdir():
            if path.suffix in ('.log','.jsonl') or path.name in ('cleanup.json','frame.bgra','native-config.json'):
                shutil.copyfile(path,out/path.name)
        write_json(out/'identity.json',self.info)
        return out

def cell_check(client,x,y,lx=None,ly=None):
    lx=lx or x; ly=ly or y
    for z in (1,0):
        before=client.snapshot()['state']['midi_count']; client.press(x,y,z)
        observed=client.wait(lambda o:o['state']['midi_count']>=before+1,'grid callback missing')
        assert observed['state']['midi'][-1]['bytes']==[176 if z else 177,lx,ly],('coordinate callback',observed['state']['midi'][-1])
        assert observed['state']['grid'][(y-1)*16+x-1]==z*15,'missing release or wrong physical LED'

def conformance():
    c=Client()
    try:
        assert c.snapshot()['state']['grid_device']['serial']=='emu-grid-128'
        # Every cell covers every corner, row, column and the native 8-column seam.
        for y in range(1,9):
            for x in range(1,17): cell_check(c,x,y)
        c.press(1,1,1); c.press(16,8,1)
        assert len(c.snapshot()['state']['held'])==2
        try: c.press(1,1,1)
        except ContractError as e: assert e.code=='duplicate_grid_transition'
        else: raise AssertionError('duplicate press accepted')
        c.press(1,1,0)
        assert len(c.snapshot()['state']['held'])==1
        assert c.snapshot()['state']['grid'][-1]==15
        c.action(type='release_all'); assert not c.snapshot()['state']['held']
        for level in range(16):
            c.action(type='enc',n=3,delta=level+1)
            assert c.snapshot()['state']['grid']==[level]*128
        c.action(type='enc',n=3,delta=1)
        c.key(2); assert c.snapshot()['state']['grid']==[0]*128,'LED change visible before refresh'
        c.key(3); assert c.snapshot()['state']['grid']==list(range(16))*8,'nonuniform bulk image differs'
        c.key(3); assert c.snapshot()['state']['grid']==[15]*128,'relative upper clamp'
        c.key(3); assert c.snapshot()['state']['grid']==[0]*128,'relative lower clamp'
        for rotation,expected in [(1,(6,2)),(2,(15,6)),(3,(3,15)),(0,(2,3))]:
            c.action(type='enc',n=1,delta=rotation or 4)
            assert c.snapshot()['state']['grid_device']['rotation']==rotation
            cell_check(c,2,3,*expected)
        for level in (0,7,15):
            c.action(type='enc',n=2,delta=level+1)
            assert c.snapshot()['state']['grid_device']['intensity']==level
        c.press(1,1,1); c.press(16,8,1)
        c.action(type='grid_connection',connected=False)
        down=c.snapshot(); assert not down['state']['held'] and down['state']['grid']==[0]*128
        assert not down['state']['grid_device']['connected']
        assert down['state']['midi'][-1]['bytes']==[176,119,0]
        try: c.press(1,1,1)
        except ContractError as e: assert e.code=='grid_disconnected'
        else: raise AssertionError('disconnected input accepted')
        c.action(type='grid_connection',connected=True)
        assert c.snapshot()['state']['midi'][-1]['bytes']==[176,119,1]
        cell_check(c,1,1); cell_check(c,16,8)
        wire=[json.loads(line) for line in (session.SESSIONS/c.sid/'native-events.jsonl').read_text().splitlines()]
        coordinates=[e['args'] for e in wire if e['kind']=='input' and e['type']==3]
        assert coordinates[:256]==[[x,y,z] for y in range(8) for x in range(16) for z in (1,0)],'raw grid transport coordinates'
        return dict(name='grid-contract',passed=True,checks='128 cells, levels 0–15, bulk/refresh, relative clamps, four rotations, intensity, holds, duplicates, reconnect')
    finally: c.finish('conformance')

def mosaic():
    c=Client(fixture=True)
    try:
        # README global menu mapping, pinned lib/pages/pages.lua and button.lua:
        # selected ordinary buttons=15; pattern mode levels=5,10,15; inactive=2.
        for x,level in [(3,15),(4,15),(5,5),(5,10),(5,15),(6,15),(3,15)]:
            c.press(x,8,1); c.press(x,8,0)
            c.wait(lambda o:o['state']['grid'][112+x-1]==level,'Mosaic menu LED did not select expected page')
        c.action(type='grid_connection',connected=False)
        assert c.snapshot()['state']['grid']==[0]*128
        c.action(type='grid_connection',connected=True)
        c.press(4,8,1); c.press(4,8,0)
        c.wait(lambda o:o['state']['grid'][115]==15,'Mosaic navigation failed after reconnect')
        return dict(name='mosaic-navigation',passed=True)
    finally: c.finish('mosaic')

def faults():
    results=[]
    original=(ROOT/'fixtures/probes/grid-probe/grid-probe.lua').read_text()
    marker='    -- Fault injection marker: coordinates and release must remain unchanged.'
    for name,change in [('swapped-coordinates','    x,y=y,x'),('missing-release','    if z==0 then return end')]:
        code=ROOT/'artifacts/c03/faults'/name/'code'; entry=code/'grid-probe/grid-probe.lua'
        entry.parent.mkdir(parents=True,exist_ok=True); entry.write_text(original.replace(marker,change))
        c=Client(entry,code)
        try:
            try: cell_check(c,2,3)
            except AssertionError as error:
                expected='coordinate callback' if name=='swapped-coordinates' else 'grid callback missing'
                assert expected in str(error),str(error)
                results.append(dict(name=name,passed=True,detected=str(error)))
            else: raise AssertionError('Seeded fault was not detected: '+name)
        finally: c.finish('fault-'+name)
    return results

if __name__=='__main__':
    identity=source_identity(); results=[]
    try:
        results.append(conformance()); print('PASS grid conformance',flush=True)
        results.append(mosaic()); print('PASS Mosaic navigation',flush=True)
        results.extend(faults()); print('PASS seeded coordinate/release fault detection',flush=True)
        from automation import runner,evidence
        for name in ('native-grid-contract','mosaic-grid-navigation'):
            path,value=runner.run(ROOT/'fixtures/scenarios'/(name+'.json'))
            assert value['passed'],value['error']; evidence.verify(path)
            results.append(dict(name=name,passed=True,manifest=str(path)))
        assert source_identity()['digest']==identity['digest'],'Source changed during suite'
        write_json(ROOT/'artifacts/c03/results.json',dict(passed=True,collected=len(results),results=results,source=identity))
    except Exception as error:
        write_json(ROOT/'artifacts/c03/results.json',dict(passed=False,results=results,error=repr(error),source=identity)); raise
