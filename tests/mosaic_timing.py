"""Real Mosaic swing: physical controls and literal musical timing tables."""
import sys,time,platform,traceback
from pathlib import Path
from mosaic_slice import Slice
from automation.protocol import ROOT,write_json,uid,checked
from automation.identity import source_identity,artifact
from automation.evidence import verify
from automation import session

def set_tempo(c,bpm):
    roots=c.snapshot()['diagnostics']['parameter_roots']
    offset=next(i for i,p in enumerate(roots) if p['id']=='CLOCK')
    c.key(1);c.action(type='enc',n=1,delta=8);c.key(3)
    c.enc(2,offset);c.key(3);c.enc(2,1)
    for _ in range(100):
        current=c.snapshot()['diagnostics']['tempo']
        if current==bpm:break
        c.enc(3,1 if current<bpm else -1)
    else:raise AssertionError('Native tempo control did not reach '+str(bpm))
    c.key(1)

def run():
    out=ROOT/'artifacts/c07'/uid();out.mkdir(parents=True)
    source=source_identity();checks=[];phases=[];failure=None;c=None
    def passed(name):checks.append(dict(name=name,passed=True))
    try:
        c=Slice(random_seed=42);c.output_root=out
        set_tempo(c,120);c.configure()
        c.enc(1,-1) # Device Config -> Clocks
        c.enc(2,1);c.enc(3,1);c.key(3) # explicitly choose Swing instead of inherited X
        c.enc(2,1);c.enc(3,76);c.key(3) # inherited -51 sentinel -> +25 percent
        c.enc(1,-3);c.enc(2,2);c.enc(3,8) # Masks starts on Note; two selections -> Length, eighth value 1/2
        passed('tempo-and-pattern-setup')
        before=c.snapshot()['midi_count'];c.tap(1,8)
        assert c.snapshot()['diagnostics']['tempo']==120
        state=c.wait(lambda s:len(c.notes(s,before))>=16)
        notes=c.notes(state,before)[:16]
        assert [m['bytes'][1:] for m in notes]==[[n,v] for _ in range(4) for n,v in ((60,127),(62,117),(64,107),(65,97))],[(m['index'],m['bytes']) for m in notes]
        # Sixteenths at 120 BPM are 24 of Mosaic's 96 quarter-note pulses.
        # +25% swing is 30/18 pulses, exactly integral: no rounding is needed.
        ticks=[48*(i//2)+(30 if i%2 else 0) for i in range(16)]
        anchor=notes[0]['monotonic_ns'];report=[]
        for note,pulse in zip(notes,ticks):
            expected=pulse/192;actual=(note['monotonic_ns']-anchor)/1e9
            report.append(dict(pitch=note['bytes'][1],intent_seconds=expected,rounded_pulse=pulse,expected_seconds=expected,actual_seconds=actual,error_ms=1000*(actual-expected)))
        write_json(out/'results.json',checked('timing-report',dict(session_id=c.sid,timing=report)))
        assert all(abs(row['error_ms'])<=10 for row in report),report
        passed('swing-playback')
        # Pinned lattice phases start at one and increment before fractional
        # delayed actions are checked: ceil(period*length)-2 pulses after onset.
        # Half of 30/18 is 15/9 intended pulses, dispatched at literal 13/7.
        durations=[]
        for i,note in enumerate(notes[:15]):
            off=next(m for m in state['midi'] if m['index']>note['index'] and m['port']==1 and m['bytes']==[128,note['bytes'][1],note['bytes'][2]])
            intended=(15 if i%2==0 else 9)/192
            pulses=13 if i%2==0 else 7
            actual=(off['monotonic_ns']-note['monotonic_ns'])/1e9
            durations.append(dict(pitch=note['bytes'][1],intent_seconds=intended,dispatch_pulses=pulses,expected_seconds=pulses/192,actual_seconds=actual,error_ms=1000*(actual-pulses/192)))
        write_json(out/'results.json',checked('timing-report',dict(session_id=c.sid,timing=report,note_durations=durations)))
        assert all(abs(row['error_ms'])<=10 for row in durations),durations
        passed('fractional-note-durations')
        c.tap(1,8);c.wait(lambda s:s['midi_capture']['outstanding']==[])
        stopped=c.snapshot()['midi_count']
        from automation.timeline import Timeline
        def observe():c.snapshot();return c.observations[-1]
        timeline=Timeline(observe,time.monotonic()+3)
        timeline.anchor('stopped');timeline.wait(dict(anchor='stopped',beats=.75,timeout_ms=2000))
        assert c.notes(c.snapshot(),stopped)==[],'Stopped sequencer emitted more notes'
        passed('stop-and-silence')
        c.tap(1,8);state=c.wait(lambda s:len(c.notes(s,stopped))>=8)
        assert [m['bytes'][1:] for m in c.notes(state,stopped)[:8]]==[[n,v] for _ in range(2) for n,v in ((60,127),(62,117),(64,107),(65,97))]
        c.tap(1,8);c.wait(lambda s:s['midi_capture']['outstanding']==[])
        passed('restart-playback')
        log=(session.SESSIONS/c.sid/'matron.log').read_text()
        assert 'applied=42' in log
        assert any('emulator random seed override: requested=1' in line and 'applied=42' in line for line in log.splitlines()),'Mosaic os.time reseed did not pass through the explicit policy'
        c.success=True
    except Exception as error:failure=dict(type=type(error).__name__,message=str(error),traceback=traceback.format_exc())
    finally:
        if c:
            try:
                directory=c.finish('transport')
                phases.append(dict(role='transport',directory=directory.relative_to(out).as_posix(),session_id=c.sid))
                passed('cleanup')
            except Exception as error:failure=failure or dict(type=type(error).__name__,message=str(error),traceback=traceback.format_exc())
    if failure:write_json(out/'failure.json',failure)
    manifest=checked('package-run',dict(schema_version=1,kind='native-package',run_id=out.name,scenario_id='A07-sequencer-start-and-stop',
        backend='native',fidelity='native-norns',tier='E',family='A07',clock_mode='real-time',source=source,
        platform=dict(profile='wsl' if 'microsoft' in platform.release().lower() else 'linux',kernel=platform.release()),
        collected=len(checks),passed=failure is None,exit_code=int(failure is not None),checks=checks,phases=phases,error=failure,
        artifacts=[artifact(p,out) for p in sorted(out.rglob('*')) if p.is_file()]))
    write_json(out/'manifest.json',manifest)
    if failure:raise AssertionError(str(failure)+'; '+str(out/'manifest.json'))
    verify(out/'manifest.json');print('Verified Mosaic transport: '+str(out/'manifest.json'),flush=True)
    return out/'manifest.json'

if __name__=='__main__':run()
