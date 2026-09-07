"""Actual Mosaic pattern editing with literal grid and MIDI expectations."""
import sys,time,platform,traceback,copy
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tests'))
from mosaic_slice import Slice
from automation.protocol import ROOT,write_json,checked,uid
from automation.identity import source_identity,artifact
from automation.evidence import verify

def check_notes(actual,expected):
    assert actual==expected,dict(expected=expected,actual=actual)

def run():
    out=ROOT/'artifacts/c08'/uid();out.mkdir(parents=True)
    source=source_identity();checks=[];phases=[];results=[];failure=None;c=None
    def passed(name):checks.append(dict(name=name,passed=True))
    def leds(expected):
        state=c.wait(lambda s:s['grid'][48:53]==expected)
        results.append(dict(kind='grid',expected=expected,actual=state['grid'][48:53]))
    def playback(expected):
        before=c.snapshot()['midi_count'];c.tap(1,8)
        state=c.wait(lambda s:len(c.notes(s,before))>=len(expected)*2)
        actual=[m['bytes'][1:] for m in c.notes(state,before)]
        wanted=[expected[i%len(expected)] for i in range(len(actual))]
        check_notes(actual,wanted)
        c.tap(1,8);c.wait(lambda s:s['midi_capture']['outstanding']==[])
        results.append(dict(kind='midi',expected=wanted,actual=actual))
    try:
        c=Slice(random_seed=42);c.output_root=out
        c.screen_header('Ch. 1 Note Masks');c.configure();c.screen_header('Ch. 1 Device Config')
        c.tap(5,8);leds([15,15,15,15,2])
        playback([[60,127],[62,117],[64,107],[65,97]])
        passed('create-pattern-and-play')
        c.tap(3,4);leds([15,15,2,15,2])
        playback([[60,127],[62,117],[65,97]])
        c.tap(3,4);leds([15,15,15,15,2])
        playback([[60,127],[62,117],[64,107],[65,97]])
        passed('remove-and-restore-trig')
        c.tap(5,8);c.tap(3,3)
        c.wait(lambda s:s['grid'][34]==12)
        playback([[60,127],[62,117],[67,107],[65,97]])
        passed('edit-note-through-grid')
        c.tap(5,8);c.tap(2,4)
        c.wait(lambda s:s['grid'][49]==12)
        playback([[60,127],[62,97],[67,107],[65,97]])
        passed('edit-velocity-through-grid')
        c.tap(5,8);leds([15,15,15,15,2])
        playback([[60,127],[62,97],[67,107],[65,97]])
        passed('page-cycle-retains-edits')
        wanted=results[-1]['expected'];mutant=copy.deepcopy(wanted);mutant[0][0]+=1
        try:check_notes(mutant,wanted)
        except AssertionError:passed('wrong-pitch-fault-rejected')
        else:raise AssertionError('Pitch oracle accepted an altered pitch')
        c.success=True
    except Exception as error:failure=dict(type=type(error).__name__,message=str(error),traceback=traceback.format_exc())
    finally:
        if c:
            try:
                directory=c.finish('editing');phases.append(dict(role='editing',directory=directory.relative_to(out).as_posix(),session_id=c.sid));passed('cleanup')
            except Exception as error:failure=failure or dict(type=type(error).__name__,message=str(error),traceback=traceback.format_exc())
    write_json(out/'results.json',results)
    if failure:write_json(out/'failure.json',failure)
    manifest=checked('package-run',dict(schema_version=1,kind='native-package',run_id=out.name,scenario_id='A04-pattern-editor',
        backend='native',fidelity='native-norns',tier='E',family='A04',clock_mode='real-time',source=source,
        platform=dict(profile='wsl' if 'microsoft' in platform.release().lower() else 'linux',kernel=platform.release()),
        collected=len(checks),passed=failure is None,exit_code=int(failure is not None),checks=checks,phases=phases,error=failure,
        artifacts=[artifact(p,out) for p in sorted(out.rglob('*')) if p.is_file()]))
    write_json(out/'manifest.json',manifest)
    if failure:raise AssertionError(str(failure)+'; '+str(out/'manifest.json'))
    verify(out/'manifest.json');print('Verified Mosaic editing: '+str(out/'manifest.json'),flush=True)
    return out/'manifest.json'

if __name__=='__main__':run()
