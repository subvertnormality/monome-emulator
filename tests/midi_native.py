"""C05 native MIDI probes: literal byte oracles, native transport and fault checks."""
import copy,json,shutil,sys,time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from automation import session
from automation.protocol import ROOT,ContractError,read_json,write_json,uid
from automation.identity import source_identity,artifact
from devices.midi import Capture
import app_fixtures

class Client:
    def __init__(self,mosaic=False,limit=1000000):
        options=app_fixtures.launch_options('mosaic','base-midi') if mosaic else dict(script=ROOT/'fixtures/probes/midi-probe/midi-probe.lua',code_root=ROOT/'fixtures/probes')
        if mosaic:options['data_seeds']=[dict(source=str(ROOT/'fixtures/apps/mosaic-config/minimal'),destination='mosaic/config',format='json-files')]
        self.info=session.start('native',midi_config=dict(ports=['Emulator MIDI','Second MIDI','Norns2sinfonion'],capture_limit=limit),**options)
        self.sid=self.info['session_id'];self.seq=0;self.observations=[]
    def action(self,**body):
        value=session.request(self.sid,'/action',dict(schema_version=1,session_id=self.sid,action_id=uid(),sequence=self.seq+1,action=body))
        self.seq+=1;return value
    def snapshot(self):
        value=session.request(self.sid,'/snapshot');self.observations.append(value);return value['state']
    def tap(self,x,y):
        self.action(type='grid',x=x,y=y,state=1);self.action(type='grid',x=x,y=y,state=0);time.sleep(.06)
    def key(self,n):
        self.action(type='key',n=n,state=1);self.action(type='key',n=n,state=0);time.sleep(.06)
    def enc(self,n,steps):
        for _ in range(abs(steps)):
            time.sleep(.05);self.action(type='enc',n=n,delta=2 if steps>0 else -2)
        time.sleep(.15)
    def wait(self,predicate):
        end=time.monotonic()+3
        while time.monotonic()<end:
            state=self.snapshot()
            if predicate(state):return state
            time.sleep(.03)
        raise AssertionError('Expected native MIDI/grid observation did not arrive')
    def finish(self,name):
        session.stop(self.sid);source=session.SESSIONS/self.sid;out=ROOT/'artifacts/c05'/name/self.sid;out.mkdir(parents=True)
        for p in source.iterdir():
            if p.suffix in ('.log','.jsonl') or p.name in ('cleanup.json','native-config.json','frame.bgra'):shutil.copyfile(p,out/p.name)
        assert all(c['returncode']==0 for c in read_json(out/'cleanup.json') if c['service']!='sclang')
        write_json(out/'observations.json',self.observations)
        # Public summaries never contain the authentication token from session metadata.
        write_json(out/'identity.json',{k:v for k,v in self.info.items() if k in ('session_id','runtime_identity','application_identity','emulator_identity')})
        return out

def exact(actual,expected):
    assert [(m['port'],m['bytes']) for m in actual]==expected,'MIDI port/channel/byte/count mismatch'

def roundtrip():
    c=Client()
    try:
        c.key(2);state=c.snapshot();expected=[]
        for channel in range(16):
            for port in (1,2,3):
                expected.extend((port,raw) for raw in ([144+channel,60,100],[128+channel,60,0],[176+channel,0,0],[176+channel,127,127],[192+channel,127]))
        exact(state['midi'],expected);assert state['midi_capture']['outstanding']==[]
        for port in (1,2,3):
            for raw,received in [([144,60,248,100,61,0,60,0],[[248],[144,60,100],[144,61,0],[144,60,0]]),
                ([240,1,248,2,3,4,247],[[248],[240,1,2],[3,4,247]]),
                ([250,251,252,254,255,242,1,2,243,127],[[250],[251],[252],[254],[255],[242,1,2],[243,127]])]:
                before=c.snapshot()['midi_count'];c.action(type='midi',port=port,bytes=raw)
                actual=c.snapshot()['midi'][before:];exact(actual,[(port,r) for r in received])
        for port in (1,2,3):
            # Native parser state survives input packet boundaries and 128-byte chunks.
            c.action(type='midi',port=port,bytes=[159,64]);c.action(type='midi',port=port,bytes=[100,64,0])
            c.action(type='midi',port=port,bytes=[248]*300)
        assert c.snapshot()['midi_capture']['outstanding']==[]
        scheduled=time.monotonic_ns()+200000000
        c.action(type='midi',port=2,bytes=[248],at_monotonic_ns=scheduled)
        assert c.snapshot()['midi'][-1]['monotonic_ns']>=scheduled
        for body,code in [(dict(type='midi',port=4,bytes=[248]),'midi_port'),(dict(type='midi',port=1,bytes=[244]),'midi_status'),(dict(type='midi',port=1,bytes=[248],at_monotonic_ns=0),'midi_input_time')]:
            try:c.action(**body);raise AssertionError('invalid input accepted')
            except ContractError as error:assert error.code==code
        captured=c.snapshot()['midi']; timestamps=[m['monotonic_ns'] for m in captured]
        assert timestamps==sorted(timestamps)
        # The exact oracle rejects both wrong channel and a missing note release.
        for mutation in ('channel','release'):
            mutant=copy.deepcopy(state['midi'])
            if mutation=='channel':mutant[0]['bytes'][0]=145
            else:mutant.pop(1)
            try:exact(mutant,expected);raise RuntimeError('fault escaped')
            except AssertionError:pass
        # Source sequence guard independently rejects a lost captured emission.
        capture=Capture(['a','b','c'],1000000)
        try:capture.accept(2,1,1,[248]);raise AssertionError('drop escaped')
        except ContractError as error:assert error.code=='midi_drop'
        return dict(name='native-midi-roundtrip',passed=True,emissions=c.snapshot()['midi_count'])
    finally:roundtrip.out=c.finish('roundtrip')

def overflow():
    c=Client(limit=10)
    try:
        try:c.key(2);raise AssertionError('overflow accepted')
        except ContractError as error:assert error.code=='midi_overflow',error
        return dict(name='native-capture-overflow',passed=True)
    finally:overflow.out=c.finish('overflow')

def mosaic():
    c=Client(mosaic=True)
    try:
        state=c.snapshot()
        exact(state['midi'],[(3,[192,0]),(3,[193,0]),(3,[194,0]),(3,[195,64]),(3,[196,0]),(3,[197,0]),(3,[198,0]),(3,[199,0]),(3,[200,64]),(3,[201,11]),(1,[252]),(2,[252]),(3,[252])])
        # Channel page: native E1 selects Device Config, E3 selects CC Device,
        # E2 selects MIDI channel/output columns. K3 commits each change.
        c.tap(3,8);c.enc(1,4);c.enc(3,1);c.key(3);time.sleep(.2)
        c.enc(2,1);c.enc(3,15);c.key(3);time.sleep(.2)
        c.enc(2,2);c.enc(3,1);c.key(3);time.sleep(.2)
        before=c.snapshot()['midi_count']
        c.action(type='midi',port=1,bytes=[144,60,90,128,60,0])
        output=c.wait(lambda s:s['midi_count']>=before+2)['midi'][before:]
        exact(output,[(2,[159,60,90]),(2,[143,60,0])])
        assert c.snapshot()['midi_capture']['outstanding']==[]
        # Change scale-slot 1 root C -> C#, confirm, then start real transport.
        c.tap(4,8);c.enc(2,-1);c.enc(3,1);c.key(3)
        before=c.snapshot()['midi_count'];c.tap(1,8)
        state=c.wait(lambda s:any(m['port']==3 and m['bytes']==[192,1] for m in s['midi'][before:]))
        assert state['grid'][115]==15
        quartet=[m['bytes'] for m in state['midi'][before:] if m['port']==3 and 192<=m['bytes'][0]<=195]
        assert quartet[:4]==[[192,1],[193,0],[194,3],[195,64]],quartet
        # Root remains C# while the scale changes from major to harmonic major.
        c.enc(2,1);c.enc(3,1);c.key(3);before=c.snapshot()['midi_count']
        state=c.wait(lambda s:any(m['port']==3 and m['bytes']==[194,7] for m in s['midi'][before:]))
        c.tap(1,8)
        assert c.snapshot()['midi_capture']['outstanding']==[]
        return dict(name='mosaic-port-channel-and-sinfonion-controls',passed=True)
    finally:mosaic.out=c.finish('mosaic')

def configs():
    paths=[]
    for name,code in [('malformed','seed_json'),('missing','seed_missing')]:
        options=app_fixtures.launch_options('mosaic','base-midi')
        options['data_seeds']=[dict(source=str(ROOT/'fixtures/apps/mosaic-config'/name),destination='mosaic/config',format='json-files')]
        try:
            info=session.start('native',**options)
            session.stop(info['session_id']);raise AssertionError('Invalid required configuration accepted')
        except ContractError as error:
            assert error.code==code,error
            directory=session.SESSIONS/error.session_id
            assert not (Path('/tmp')/('norns_emu_'+error.session_id)).exists()
            paths.append(str(directory))
    configs.out=ROOT/'artifacts/c05/configs';configs.out.mkdir(exist_ok=True)
    write_json(configs.out/'results.json',dict(passed=True,failures=paths))
    return dict(name='malformed-and-missing-configs',passed=True)

if __name__=='__main__':
    results=[];paths=[]
    try:
        for test in (roundtrip,overflow,mosaic,configs):
            result=test();results.append(result);paths.append(str(test.out));print(json.dumps(result),flush=True)
    finally:
        write_json(ROOT/'artifacts/c05/results.json',dict(source=source_identity(),results=results,paths=paths,collected=4,passed=len(results)==4))
