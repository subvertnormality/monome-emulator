"""Shared application-fixture driver; never imported by the emulator runtime."""
import platform,time,traceback
from mosaic_slice import Slice
from automation.protocol import ROOT,write_json,checked,uid,ContractError
from automation import session
from automation.identity import source_identity,artifact
from automation.evidence import verify
from automation.timeline import Timeline

class Workflow(Slice):
    def __init__(self,code_root=None):
        super().__init__(random_seed=42,fixture_code_root=code_root);self.checks=[];self.results=[]
        self.log_position=0;self.log_fragment=b''
    def check_scheduler_log(self):
        # Mosaic catches coroutine.resume failures and prints them. This belongs
        # to its opt-in fixture, not an application-specific runtime adapter.
        with (session.SESSIONS/self.sid/'matron.log').open('rb') as log:
            log.seek(self.log_position);chunk=log.read();self.log_position=log.tell()
        lines=(self.log_fragment+chunk).split(b'\n');self.log_fragment=lines.pop()
        for line in lines:
            if line.startswith(b'Coroutine error:'):
                raise ContractError('mosaic_coroutine_error',line.decode(errors='replace'))
    def snapshot(self):
        state=super().snapshot();self.check_scheduler_log();return state
    def passed(self,name):self.checks.append(dict(name=name,passed=True))
    def wait(self,predicate,timeout=3):
        # Keep the first and final witness of each distinct wait. Polling still
        # checks every snapshot; complete inputs/MIDI remain in native-events.
        start=len(self.observations);polls=0;end=time.monotonic()+timeout
        try:
            while time.monotonic()<end:
                state=self.snapshot();polls+=1
                if len(self.observations)>start+2:del self.observations[start+1:-1]
                if predicate(state):return state
                time.sleep(.03)
            raise AssertionError('Expected native MIDI/grid observation did not arrive')
        finally:
            self.results.append(dict(kind='poll-retention',policy='first-and-final-per-wait',
                                     polls=polls,retained=len(self.observations)-start))
    def led_values(self,cells,expected):
        indexes=[(y-1)*16+x-1 for x,y in cells]
        state=self.wait(lambda s:[s['grid'][i] for i in indexes]==expected)
        self.results.append(dict(kind='grid',cells=cells,expected=expected,actual=[state['grid'][i] for i in indexes]))
    def playback(self,expected,cycles=2,timeout=3):
        before=self.snapshot()['midi_count'];self.tap(1,8)
        def notes(s):return [m for m in s['midi'] if m['index']>before and 144<=m['bytes'][0]<=159 and m['bytes'][2]>0]
        state=self.wait(lambda s:len(notes(s))>=len(expected)*cycles,timeout=timeout)
        actual=[(m['port'],m['bytes']) for m in notes(state)]
        wanted=[expected[i%len(expected)] for i in range(len(actual))]
        assert actual==wanted,dict(expected=wanted,actual=actual)
        self.tap(1,8);self.wait(lambda s:s['midi_capture']['outstanding']==[])
        self.results.append(dict(kind='midi',expected=wanted,actual=actual))
        return notes(state)
    def hold_tap(self,held,tapped):
        self.action(type='grid',x=held[0],y=held[1],state=1)
        try:self.tap(*tapped)
        finally:self.action(type='grid',x=held[0],y=held[1],state=0)
    def shift_tap(self,x,y):
        self.action(type='key',n=1,state=1)
        time.sleep(.3) # official menu.lua's script-K1 hold threshold is 250 ms
        try:self.tap(x,y)
        finally:self.action(type='key',n=1,state=0)
    def wait_beats(self,beats):
        def observe():self.snapshot();return self.observations[-1]
        timeline=Timeline(observe,time.monotonic()+5);timeline.anchor('now')
        timeline.wait(dict(anchor='now',beats=beats,timeout_ms=4000))
        self.results.append(dict(kind='timeline',events=timeline.events))

def run_package(scenario_id,body,code_root=None):
    from automation.protocol import read_json
    spec=read_json(ROOT/'compatibility/packages.json')['packages'][scenario_id]
    role=spec['roles'][0];out=ROOT/'artifacts/c08'/uid();out.mkdir(parents=True)
    source=source_identity();failure=None;c=None;phases=[];checks=[];results=[]
    try:
        if spec.get('candidate_manifest'):
            assert code_root is not None,'Required patched application candidate was not selected'
            write_json(out/'candidate.json',read_json(code_root.parent/'candidate.json'))
        c=Workflow(code_root);c.output_root=out;body(c);c.success=True
    except Exception as error:failure=dict(type=type(error).__name__,message=str(error),traceback=traceback.format_exc())
    finally:
        if c:
            try:
                directory=c.finish(role);phases.append(dict(role=role,directory=directory.relative_to(out).as_posix(),session_id=c.sid));c.passed('cleanup')
                c.check_scheduler_log()
            except Exception as error:failure=failure or dict(type=type(error).__name__,message=str(error),traceback=traceback.format_exc())
            checks=c.checks;results=c.results
    write_json(out/'results.json',results)
    if failure:write_json(out/'failure.json',failure)
    manifest=checked('package-run',dict(schema_version=1,kind='native-package',run_id=out.name,scenario_id=scenario_id,
        backend='native',fidelity='native-norns',tier='E',family=spec['family'],clock_mode='real-time',source=source,
        platform=dict(profile='wsl' if 'microsoft' in platform.release().lower() else 'linux',kernel=platform.release()),
        collected=len(checks),passed=failure is None,exit_code=int(failure is not None),checks=checks,phases=phases,error=failure,
        artifacts=[artifact(p,out) for p in sorted(out.rglob('*')) if p.is_file()]))
    write_json(out/'manifest.json',manifest)
    if failure:raise AssertionError(str(failure)+'; '+str(out/'manifest.json'))
    verify(out/'manifest.json');print('Verified '+scenario_id+': '+str(out/'manifest.json'),flush=True)
    return out/'manifest.json'
