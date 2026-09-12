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
        self.seq+=1; self.trace.append(dict(request=request,ack=ack)); return ack
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
        out=getattr(self,'output_root',ROOT/'artifacts/c03')/name; out.mkdir(parents=True,exist_ok=True)
        write_json(out/'trace.json',self.trace); write_json(out/'observations.json',self.observations)
        for path in directory.iterdir():
            if path.suffix in ('.log','.jsonl') or path.name in ('cleanup.json','frame.bgra','native-config.json'):
                shutil.copyfile(path,out/path.name)
        write_json(out/'identity.json',{k:v for k,v in self.info.items() if k in ('session_id','runtime_identity','application_identity','emulator_identity')})
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

def timed_controls():
    """Real-time deadlines reach the unchanged native control packet path."""
    c=Client()
    checks=[]
    try:
        transitions=[
            (dict(type='grid',x=8,y=4,state=1),3,[7,3,1]),
            (dict(type='grid',x=8,y=4,state=0),3,[7,3,0]),
            (dict(type='enc',n=3,delta=5),2,[3,5]),
            (dict(type='key',n=2,state=1),1,[2,1]),
            (dict(type='key',n=2,state=0),1,[2,0]),
        ]
        for action,native_type,native_args in transitions:
            due=time.monotonic_ns()+150_000_000
            began=time.monotonic_ns()
            ack=c.action(**dict(action,at_monotonic_ns=due))
            returned=time.monotonic_ns()
            assert returned>=due,(action,due,returned)
            assert returned-began>=125_000_000,(action,began,returned)
            events=[json.loads(line) for line in
                    (session.SESSIONS/c.sid/'native-events.jsonl').read_text().splitlines()]
            matches=[e for e in events if e.get('kind')=='input' and
                     e.get('sequence')==ack['native']['sequence']]
            assert len(matches)==1,(action,matches)
            event=matches[0]
            assert event['type']==native_type and event['args']==native_args,(action,event)
            lateness=event['monotonic_ns']-due
            assert 0<=lateness<=25_000_000,(action,lateness)
            checks.append(dict(action=action,due_ns=due,applied_ns=event['monotonic_ns'],
                               lateness_ns=lateness,native_sequence=event['sequence']))
        assert c.snapshot()['state']['held']==[]
        return dict(name='timed-controls',passed=True,checks=checks,
                    bound_ns=25_000_000)
    finally:c.finish('timed-controls')

def scheduled_gesture():
    """One acknowledged submission carries both transitions before either is due."""
    c=Client()
    try:
        due=time.monotonic_ns()+350_000_000
        events=[
            dict(type='grid',x=8,y=4,state=1,at_monotonic_ns=due),
            dict(type='grid',x=8,y=4,state=0,at_monotonic_ns=due+60_000_000),
            dict(type='key',n=2,state=1,at_monotonic_ns=due+80_000_000),
            dict(type='key',n=2,state=0,at_monotonic_ns=due+120_000_000),
            dict(type='enc',n=3,delta=5,at_monotonic_ns=due+140_000_000),
        ]
        ack=c.action(type='native_input_schedule',schedule_id=1,events=events)
        submitted=time.monotonic_ns()
        assert ack['status']=='accepted' and submitted<due,(ack,submitted,due)
        accepted=c.snapshot()['state']['native_input_schedule']
        assert accepted['status']=='accepted' and accepted['events']==events,accepted
        try:c.action(type='grid',x=1,y=1,state=1)
        except ContractError as error:assert error.code=='schedule_busy',error
        else:raise AssertionError('Immediate input bypassed an admitted schedule')
        finished=c.wait(lambda o:o['state']['native_input_schedule']['status']=='completed','native control schedule did not complete')
        record=finished['state']['native_input_schedule']
        assert [event['index'] for event in record['delivered']]==list(range(len(events))),record
        wire=[json.loads(line) for line in (session.SESSIONS/c.sid/'native-events.jsonl').read_text().splitlines()]
        wanted=[(3,[7,3,1]),(3,[7,3,0]),(1,[2,1]),(1,[2,0]),(2,[3,5])]
        actual=[(event['type'],event['args']) for event in wire if event.get('kind')=='input' and event['type'] in (1,2,3)][-len(wanted):]
        assert actual==wanted,(actual,wanted)
        for event,delivery in zip(events,record['delivered']):
            assert delivery['action']=={key:value for key,value in event.items() if key!='at_monotonic_ns'}
            assert delivery['callback_completed_monotonic_ns']==delivery['applied_monotonic_ns'],delivery
            assert 0<=delivery['applied_monotonic_ns']-event['at_monotonic_ns']<=25_000_000,delivery
        grid_callback=[event for event in wire if event.get('kind')==3 and event.get('bytes')==[176,8,4]]
        assert grid_callback and grid_callback[-1]['monotonic_ns']<=record['delivered'][0]['callback_completed_monotonic_ns'],(grid_callback,record)
        assert c.snapshot()['state']['held']==[]
        invalid=[
            (dict(type='native_input_schedule',schedule_id=2,events=[dict(type='grid',x=1,y=1,state=1,at_monotonic_ns=time.monotonic_ns()+300_000_000),dict(type='grid',x=1,y=1,state=1,at_monotonic_ns=time.monotonic_ns()+350_000_000)]),'duplicate_grid_transition'),
            (dict(type='native_input_schedule',schedule_id=3,events=[dict(type='enc',n=1,delta=1,at_monotonic_ns=time.monotonic_ns()+350_000_000),dict(type='enc',n=1,delta=1,at_monotonic_ns=time.monotonic_ns()+300_000_000)]),'input_schedule_order'),
        ]
        for action,code in invalid:
            try:c.action(**action)
            except ContractError as error:assert error.code==code,error
            else:raise AssertionError('Invalid native control schedule was accepted: '+code)
        return dict(name='native-control-schedule',passed=True,submitted_ns=submitted,due_ns=due,deliveries=record['delivered'])
    finally:c.finish('scheduled-gesture')

def scheduled_shutdown():
    """Shutdown terminally records, rather than races, an admitted gesture."""
    c=Client()
    try:
        due=time.monotonic_ns()+1_000_000_000
        ack=c.action(type='native_input_schedule',schedule_id=1,events=[
            dict(type='key',n=2,state=1,at_monotonic_ns=due),
            dict(type='key',n=2,state=0,at_monotonic_ns=due+50_000_000),
        ])
        assert ack['status']=='accepted'
        session.stop(c.sid)
        records=[json.loads(line) for line in (session.SESSIONS/c.sid/'native-input-schedules.jsonl').read_text().splitlines()]
        terminal=records[-1]
        assert terminal['kind']=='cancelled',terminal
        assert terminal['schedule']['status']=='cancelled',terminal
        assert terminal['schedule']['schedule_id']==1,terminal
        return dict(name='native-control-schedule-shutdown',passed=True,terminal=terminal)
    finally:c.finish('scheduled-shutdown')

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
        results.append(timed_controls()); print('PASS timed physical controls',flush=True)
        results.append(scheduled_gesture()); print('PASS native control schedule',flush=True)
        results.append(scheduled_shutdown()); print('PASS scheduled control shutdown',flush=True)
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
