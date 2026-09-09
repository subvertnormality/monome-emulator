"""Pinned norns delivers Continue/SPP to Lua without treating them as Start."""
import argparse,hashlib,json,sys,time,uuid
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from automation.client import Session
def main():
    parser=argparse.ArgumentParser();parser.add_argument('--install',required=True)
    parser.add_argument('--clock-mode',choices=['controlled-experimental','real-time'],required=True)
    args=parser.parse_args();out=ROOT/'artifacts/midi-clock'/uuid.uuid4().hex;out.mkdir(parents=True)
    failure=None;observations={};phase_identities={}
    controlled=args.clock_mode=='controlled-experimental';domain='logical' if controlled else 'monotonic'
    def run_probe(name,relative_packets,expected):
        session=None
        try:
            session=Session(script=ROOT/'fixtures/probes/midi-continue-spp/midi-continue-spp.lua',code_root=ROOT/'fixtures/probes',clock_mode=args.clock_mode,experimental_install=args.install,random_seed=42)
            origin=500_000_000 if controlled else time.monotonic_ns()+500_000_000
            events=[dict(port=1,bytes=data,**{'at_'+domain+'_ns':origin+offset}) for offset,data in relative_packets]
            request=dict(type='midi_schedule',schedule_id=401,events=events)
            if controlled:request['time_domain']='logical'
            session.action(request)
            end=max(offset for offset,_ in relative_packets)+250_000_000
            if controlled:session.action(dict(type='advance',nanoseconds=origin+end))
            else:time.sleep((500_000_000+end)/1e9)
            state=session.observe();observations[name]=state
            assert len(state['state']['midi_input_schedule']['delivered'])==len(events)
            capture=state['state']['midi_capture'];output_events=state['state']['midi']
            assert capture['dropped']==0 and capture['count']==state['state']['midi_count']==len(output_events)
            assert [event['index'] for event in output_events]==list(range(1,len(output_events)+1))
            output=[event['bytes'] for event in output_events if event['port']==1]
            assert len(output)==len(output_events)
            assert output==expected,(name,output,expected)
        finally:
            if session:
                native=out/('native-'+name);session.close(native)
                identity=native/'identity.json'
                phase_identities[name]=dict(path=str(identity),sha256=hashlib.sha256(identity.read_bytes()).hexdigest())
    try:
        warm=[(i*25_000_000,[248]) for i in range(1,50)]
        run_probe('transport',warm+[(1_250_000_000,[250]),(1_250_000_000,[248]),(1_275_000_000,[252])],[[176,10,1],[176,11,1]])
        run_probe('continue',[(0,[251])]+[((i+1)*25_000_000,[248]) for i in range(4)],[[176,20,1]])
        run_probe('song-position',[(0,[242,5,1])]+[((i+1)*25_000_000,[248]) for i in range(4)],[[176,21,5],[176,22,1]])
    except Exception as error:
        failure=dict(type=type(error).__name__,message=str(error))
    (out/'observations.json').write_text(json.dumps(observations,indent=2)+'\n')
    result=dict(passed=failure is None,failure=failure,clock_mode=args.clock_mode,install=args.install,phase_identities=phase_identities,scope='Generic pinned-norns phase-isolated Continue/SPP delivery and transport classification; no Mosaic')
    (out/'manifest.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(dict(path=str(out/'manifest.json'),**result)),flush=True)
    if failure:raise SystemExit(1)
if __name__=='__main__':main()
