"""Actual official arc callbacks, ring LEDs, reconnect and grid independence."""
import argparse,time
from pathlib import Path
from audio_feasibility import ROOT,source_identity,write_json
from automation.client import Session
from automation.protocol import ContractError

def main():
    p=argparse.ArgumentParser();p.add_argument('--install',required=True,type=Path);a=p.parse_args()
    out=ROOT/'artifacts/arc'/time.strftime('native-%Y%m%d-%H%M%S');out.mkdir(parents=True)
    report=dict(passed=False,source=source_identity(),checks=[]);client=None
    try:
        client=Session(script=ROOT/'fixtures/probes/arc-probe/arc-probe.lua',code_root=ROOT/'fixtures/probes',experimental_install=a.install,crow_enabled=False,arc_enabled=True)
        def act(**action):return client.action(action)
        def snap():
            value=client.observe()['state'];assert value['grid'][0]==9 and sum(value['grid'])==9
            assert value['grid_device']['intensity']==15
            return value
        def check(name):report['checks'].append(dict(name=name,passed=True));print('PASS '+name,flush=True)
        def expected(positions):
            rings=[[0]*64 for _ in range(4)]
            for n,pos in enumerate(positions):rings[n][pos-1]=(n+1)*3
            return rings
        state=snap();assert state['arc_device']['enabled'] and state['arc_device']['connected']
        assert state['arc']==expected([8,16,24,32]);check('four-native-rings-and-independent-grid')
        act(type='enc',n=3,delta=2)
        assert snap()['arc'][1][15]==1
        check('official-relative-led-level')
        positions=[8,16,24,32]
        for n,d in [(1,3),(2,-2),(3,-27),(4,70)]:
            ack=act(type='arc_delta',n=n,delta=d);assert ack['native']['sequence']>0
            positions[n-1]=(positions[n-1]-1+d)%64+1
            state=snap();assert state['arc']==expected(positions)
            assert state['midi'][-1]['bytes']==[176,n,positions[n-1]]
        check('relative-native-deltas-and-wrapping')
        act(type='arc_key',n=2,state=1);assert snap()['arc'][1][63]==15
        act(type='arc_connection',connected=False);state=snap()
        assert not state['arc_device']['connected'] and not state['held']
        assert not any(sum(ring) for ring in state['arc'])
        assert [176,22,0] in [row['bytes'] for row in state['midi'][-4:]]
        try:act(type='arc_delta',n=1,delta=1)
        except ContractError as e:assert e.code=='arc_disconnected',e
        else:raise AssertionError('Disconnected arc accepted input')
        check('disconnect-releases-native-key-and-rejects-input')
        act(type='arc_connection',connected=True);assert snap()['arc']==expected(positions)
        act(type='arc_key',n=1,state=1);act(type='release_all');assert not snap()['held']
        check('reconnect-and-release-all')
        act(type='key',n=2,state=1);act(type='key',n=2,state=0);assert snap()['arc_device']['intensity']==5
        check('independent-arc-intensity')
        act(type='key',n=3,state=1);act(type='key',n=3,state=0)
        state=snap();assert state['arc'][:3]==[[0]*64 for _ in range(3)]
        assert state['arc'][3]==[12]*16+[0]*32+[12]*16
        check('official-angular-segment-wrap')
        other=Session(script=ROOT/'fixtures/probes/arc-probe/arc-probe.lua',code_root=ROOT/'fixtures/probes',experimental_install=a.install,crow_enabled=False,arc_enabled=True)
        try:
            assert other.id!=client.id
            assert other.observe()['state']['arc']==expected([8,16,24,32])
            other.action(dict(type='arc_delta',n=1,delta=5))
            assert other.observe()['state']['arc']==expected([13,16,24,32])
            assert snap()['arc']==state['arc']
        finally:other.close(out/'other-session')
        assert snap()['arc']==state['arc']
        check('two-session-arc-isolation-and-independent-cleanup')
        write_json(out/'final-state.json',state)
        client.close(out/'session');client=None;report['passed']=True
    except Exception as e:report['error']=repr(e);raise
    finally:
        if client:
            try:client.close(out/'session')
            except Exception as e:report['passed']=False;report['cleanup_error']=repr(e)
        write_json(out/'report.json',report);print(out,flush=True)
    assert report['passed'],report
if __name__=='__main__':main()
