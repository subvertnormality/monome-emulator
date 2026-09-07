"""External-suite client conformance against a generic native MIDI probe."""
import json,sys,uuid
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from automation.client import Session
from automation.protocol import ROOT

def run():
    out=ROOT/'artifacts/public-client'/uuid.uuid4().hex
    runtime=Session(script=ROOT/'fixtures/probes/midi-probe/midi-probe.lua',
                    code_root=ROOT/'fixtures/probes',midi_config={'ports':['Emulator MIDI']})
    failure=None
    try:
        assert runtime.capabilities()['fidelity']=='native-norns'
        runtime.action(dict(type='key',n=2,state=1));runtime.action(dict(type='key',n=2,state=0))
        state=runtime.observe()['state'];expected=[]
        for channel in range(16):
            expected.extend([[144+channel,60,100],[128+channel,60,0],
                             [176+channel,0,0],[176+channel,127,127],[192+channel,127]])
        assert [m['bytes'] for m in state['midi']]==expected
        assert state['midi_capture']['outstanding']==[]
    except Exception as error:failure=error
    finally:runtime.close(out)
    assert not (out/'session.json').exists() and not (out/'config.json').exists()
    assert (out/'native-events.jsonl').is_file() and (out/'identity.json').is_file()
    assert all(c['returncode']==0 for c in json.loads((out/'cleanup.json').read_text()) if c['service']!='sclang')
    if failure:raise failure
    print('Verified public native client, 80 exact MIDI emissions: '+str(out))

if __name__=='__main__':run()
