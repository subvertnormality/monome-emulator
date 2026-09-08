"""Optional unchanged Mosaic/n.b. player workflow through native controls."""
import argparse,json,subprocess,time
from pathlib import Path
from mosaic_slice import Slice
from audio_feasibility import capture,read_wav,metrics,silence,require
from automation.client import Session
from automation.protocol import ROOT,write_json
from automation.identity import source_identity

class AudioSlice(Slice):
    def __init__(self,client):
        self.client=client;self.info=client.info;self.sid=client.id;self.seq=0
        self.observations=[];self.browser=None;self.recipe=[];self.success=False
    def action(self,**body):
        self.recipe.append(body);return self.client.action(body)

def main():
    p=argparse.ArgumentParser();p.add_argument('--install',type=Path,required=True);a=p.parse_args()
    out=ROOT/'artifacts/audio'/time.strftime('mosaic-%Y%m%d-%H%M%S');out.mkdir(parents=True)
    code=ROOT/'.runtime/mosaic-audio/code';code.mkdir(parents=True,exist_ok=True)
    sources={'mosaic':(ROOT/'.runtime/fixtures/mosaic/code/mosaic','160d1ea7506773e65f298094e11d005dcb568dff'),
             'doubledecker':(ROOT/'.runtime/nb-player/code/doubledecker','8729b9ceee71d2b07067e89fbef5d8b98d6a0c89')}
    report=dict(passed=False,source=source_identity(),checks=[],dependencies={});client=None;c=None
    try:
        for name,(path,pin) in sources.items():
            path=path.resolve();require(subprocess.check_output(['git','rev-parse','HEAD'],cwd=path,text=True).strip()==pin,'Wrong '+name+' revision')
            require(not subprocess.check_output(['git','diff','HEAD','--'],cwd=path),'Changed '+name)
            target=code/name
            if not target.exists():target.symlink_to(path,target_is_directory=True)
            require(target.resolve()==path,'Wrong fixture link');report['dependencies'][name]=pin
        client=Session(script=code/'mosaic/mosaic.lua',code_root=code,enabled_mods=['doubledecker'],
            random_seed=42,data_seeds=[dict(source=str(ROOT/'fixtures/apps/mosaic-config/minimal'),destination='mosaic/config',format='json-files')],
            midi_config=dict(ports=['Emulator MIDI','Second MIDI','Norns2sinfonion'],capture_limit=1000000),experimental_install=a.install)
        c=AudioSlice(client);time.sleep(13)
        report['checks'].append(dict(name='baseline',metrics=silence(capture(client.id,out/'baseline.wav'))))
        c.configure();c.screen_header('Ch. 1 Device Config')
        # Existing recipe selects the built-in CC Device; DoubleDecker follows it.
        c.enc(3,1);c.key(3)
        path=capture(client.id,out/'pattern.wav',seconds=4,trigger=lambda:c.tap(1,8))
        rate,channels=read_wav(path)
        # Literal C4,D4,E4,F4 recipe; inspect actual audio, never application state.
        values=[metrics(channels[0],rate,f) for f in (261.625565,293.664768,329.627557,349.228231)]
        require(values[0]['rms']>.001,'Mosaic did not produce audio: '+str(values))
        require(all(v['tone_energy_fraction']>.005 for v in values),'Expected phrase frequencies missing: '+str(values))
        report['checks'].append(dict(name='four-note-native-pattern-audio',metrics=values))
        c.tap(1,8)
        rate,tail=read_wav(capture(client.id,out/'stopped.wav',seconds=6))
        late=[metrics(ch[-int(rate*1.5):],rate,440)['rms'] for ch in tail]
        require(max(late)<.0001,'Post-stop tail did not reach silence within six seconds: '+str(late))
        report['checks'].append(dict(name='stop-and-effects-tail-release',final_rms=late,maximum_seconds=6))
        report['passed']=True
    except Exception as error:report['error']=repr(error);raise
    finally:
        if c:write_json(out/'recipe.json',c.recipe)
        if client:
            try:client.close(out/'session')
            except Exception as error:report['passed']=False;report['cleanup_error']=repr(error)
        write_json(out/'report.json',report);print(out,flush=True)
    require(report['passed'],'Mosaic audio workflow failed')
if __name__=='__main__':main()
