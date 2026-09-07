"""C06 application-control slice, developed against actual native Mosaic."""
import json,sys,time,platform,shutil
import hashlib
from pathlib import Path
from midi_native import Client,exact
from automation.protocol import ROOT,write_json,checked,uid
from automation import session
from automation.identity import source_identity,artifact

def normalized(actions):
    result=[]
    for action in actions:
        if action['type']=='key':value=[1,action['n'],action['state']]
        elif action['type']=='grid':value=[3,action['x']-1,action['y']-1,action['state']]
        elif action['type']=='enc':value=[2,action['n'],action['delta']]
        else:raise AssertionError('Unknown recipe input')
        if value[0]==2 and result and result[-1][:2]==value[:2] and result[-1][2]*value[2]>0:result[-1][2]+=value[2]
        else:result.append(value)
    return result

class Slice(Client):
    def __init__(self,data_seed=None,browser=False,random_seed=None,fixture_code_root=None):
        super().__init__(mosaic=True,data_seed=data_seed,random_seed=random_seed,fixture_code_root=fixture_code_root);self.output_root=ROOT/'artifacts/c06'
        self.browser=None;self.recipe=[];self.success=False
        if browser:
            from browser_client import Browser
            try:self.browser=Browser(self.info['browser_url'],session.SESSIONS/self.sid)
            except Exception:session.stop(self.sid);raise
    def action(self,**body):
        self.recipe.append(dict(body))
        if self.browser:self.browser.request(dict(action=body))
        else:return super().action(**body)
    def finish(self,name):
        try:
            if self.browser:
                from browser_client import windows_path
                try:self.browser.request(dict(screenshot=windows_path(session.SESSIONS/self.sid/'browser.png'),verifyPixels=self.success))
                finally:self.browser.close();self.browser=None
        finally:out=super().finish(name)
        screenshot=session.SESSIONS/self.sid/'browser.png'
        if screenshot.exists():
            shutil.copyfile(screenshot,out/'browser.png')
        write_json(out/'recipe.json',self.recipe)
        saved=out/'saved-files';saved.mkdir()
        for file in (Path(self.info['data'])/'mosaic').iterdir():
            if file.is_file() and file.suffix in ('.ptn','.pset'):shutil.copyfile(file,saved/file.name)
        if self.success:
            raw=[json.loads(line) for line in (out/'native-events.jsonl').read_text().splitlines()]
            native=[]
            for e in raw:
                if e['kind']!='input' or e['type'] not in (1,2,3):continue
                t=e['type'];a=e['args']
                native.append(dict(type='key',n=a[0],state=a[1]) if t==1 else dict(type='enc',n=a[0],delta=a[1]) if t==2 else dict(type='grid',x=a[0]+1,y=a[1]+1,state=a[2]))
            assert normalized(native)==normalized(self.recipe),'Actual native input trace differs from workflow recipe'
            write_json(out/'normalized-inputs.json',normalized(native))
        return out
    def configure(self):
        self.tap(3,8);self.enc(1,4);self.enc(3,1);self.key(3)
        self.tap(5,8)
        for x in range(1,5):self.tap(x,4)
        self.tap(5,8)
        for x,y in ((1,7),(2,6),(3,5),(4,4)):self.tap(x,y)
        self.tap(5,8)
        for x,y in ((1,1),(2,2),(3,3),(4,4)):self.tap(x,y)
        self.tap(3,8);self.tap(1,2)
        self.action(type='grid',x=1,y=4,state=1)
        self.action(type='grid',x=4,y=4,state=1)
        self.action(type='grid',x=4,y=4,state=0)
        self.action(type='grid',x=1,y=4,state=0)
        self.wait(lambda s:s['grid'][16]==15)
    def screen_header(self,text):
        from frame_oracle import header,matches
        expected=header(text)
        # Await the named stable page, retaining every intervening observation.
        self.wait(lambda state:matches(state,expected))
        assert not matches(dict(frame=dict(pixels_base64='AAAA'*8192)),expected),'Blank-frame fault escaped the content oracle'
    def notes(self,state,start):
        return [m for m in state['midi'] if m['index']>start and m['port']==1 and m['bytes'][0]==144 and m['bytes'][2]>0]
    def play(self):
        start=self.snapshot()['midi_count'];self.tap(1,8)
        state=self.wait(lambda s:len(self.notes(s,start))>=8)
        exact(self.notes(state,start)[:8],[(1,[144,n,v]) for _ in range(2) for n,v in [(60,127),(62,117),(64,107),(65,97)]])
        self.tap(5,8);self.tap(5,8);self.tap(3,3)
        after=self.snapshot()['midi_count']
        state=self.wait(lambda s:len(self.notes(s,after))>=12)
        edited=self.notes(state,after)
        sequence=[[60,127],[62,117],[67,107],[65,97]]
        phase=[v for n,v in sequence].index(edited[0]['bytes'][2])
        assert [m['bytes'][1:] for m in edited]==[sequence[(phase+i)%4] for i in range(len(edited))]
        self.tap(1,8)
        self.wait(lambda s:s['midi_capture']['outstanding']==[])
        self.tap(3,8);self.screen_header('Ch. 1 Device Config')
        return dict(passed=True,first_eight_notes=[m['bytes'] for m in self.notes(state,start)[:8]])
    def parameter_menu(self):
        roots=self.snapshot()['diagnostics']['parameter_roots']
        offset=next(i for i,p in enumerate(roots) if p['id']=='mosaic')
        self.key(1)
        self.action(type='enc',n=1,delta=8) # upstream menu E1 sensitivity is eight ticks
        self.key(3)
        self.enc(2,offset);self.key(3)
    def save(self):
        self.parameter_menu()
        self.enc(2,1);self.key(3) # Save project trigger -> textentry default "new"
        self.key(3) # native textentry OK on key release
        saved=Path(self.info['data'])/'mosaic/new.ptn'
        end=time.monotonic()+3
        while not saved.exists() and time.monotonic()<end:time.sleep(.03)
        assert saved.is_file(), 'Native save dialog did not write new.ptn'
        assert saved.with_suffix('.pset').is_file()
        self.key(1) # exit native menu, leaving the script's original page intact
        return str(saved)
    def await_autosave(self):
        saved=Path(self.info['data'])/'mosaic/autosave.ptn'
        end=time.monotonic()+70
        while not saved.exists() and time.monotonic()<end:
            self.snapshot();time.sleep(.5)
        assert saved.exists(),'Native autosave did not complete'
        return saved
    def load(self):
        # Make the live state different so a no-op Load cannot pass by retaining
        # the project that startup already loaded from autosave.
        self.tap(3,8);self.tap(5,8);self.tap(5,8);self.tap(2,1)
        self.parameter_menu();self.enc(2,2);self.key(3)
        # File selector uses the actual directory's alphabetical entries.
        folder=Path(self.info['data'])/'mosaic'
        entries=sorted(p.name+('/' if p.is_dir() else '') for p in folder.iterdir())
        self.enc(2,entries.index('new.ptn'));self.key(3);self.key(1)
        assert ('Loading project '+str(self.info['data']).replace(str(ROOT/'.runtime/sessions'/self.sid),'/tmp/norns_emu_'+self.sid)+'/mosaic/new.ptn') in (session.SESSIONS/self.sid/'matron.log').read_text()
        before=self.snapshot()['midi_count'];self.tap(1,8)
        state=self.wait(lambda s:len(self.notes(s,before))>=8)
        exact(self.notes(state,before)[:8],[(1,[144,n,v]) for _ in range(2) for n,v in [(60,127),(62,117),(67,107),(65,97)]])
        self.tap(1,8);self.wait(lambda s:s['midi_capture']['outstanding']==[])
        return dict(passed=True,reloaded_notes=[m['bytes'] for m in self.notes(state,before)[:8]])

def run(browser=False):
    from automation.evidence import verify
    mode='browser' if browser else 'api';run_id=uid();out=ROOT/'artifacts/c06'/run_id;out.mkdir(parents=True)
    source=source_identity();checks=[];phases=[];failure=None
    def passed(name):checks.append(dict(name=name,passed=True))
    def finish(client,role):
        client.output_root=out;directory=client.finish(role)
        phases.append(dict(role=role,directory=directory.relative_to(out).as_posix(),session_id=client.sid))
    try:
        c=Slice(browser=browser)
        try:
            assert c.snapshot()['ready'] and not (Path(c.info['data'])/'mosaic/autosave.ptn').exists()
            c.screen_header('Ch. 1 Note Masks')
            passed('fresh-bootstrap')
            c.configure();result=c.play();passed('four-step-playback-and-live-edit')
            result['saved']=c.save();passed('save-dialog');print(mode+' save passed',flush=True)
            c.await_autosave();passed('native-autosave');print(mode+' native autosave passed',flush=True);c.success=True
        finally:finish(c,'fresh')
        passed('fresh-cleanup')
        restored=Slice(Path(result['saved']).parent,browser=browser)
        try:
            assert restored.snapshot()['ready']
            assert 'Loading project /tmp/norns_emu_'+restored.sid+'/dust/data/mosaic/autosave.ptn' in (session.SESSIONS/restored.sid/'matron.log').read_text()
            passed('autosave-bootstrap')
            result.update(restored.load());passed('file-dialog-load-and-playback');restored.success=True
        finally:finish(restored,'autosave')
        passed('reload-cleanup');write_json(out/'results.json',result)
    except Exception as error:
        failure=dict(type=type(error).__name__,message=str(error));write_json(out/'failure.json',failure)
    manifest=checked('package-run',dict(schema_version=1,kind='native-package',run_id=run_id,scenario_id='mosaic-four-step-'+mode,
        backend='native',fidelity='native-norns',tier='B' if browser else 'E',family='A01',clock_mode='real-time',source=source,
        platform=dict(profile='wsl' if 'microsoft' in platform.release().lower() else 'linux',kernel=platform.release(),browser='Windows Chromium 151.0.7922.34 / Playwright 1.62.1' if browser else None),
        collected=len(checks),passed=failure is None,exit_code=int(failure is not None),checks=checks,phases=phases,error=failure,
        artifacts=[artifact(p,out) for p in sorted(out.rglob('*')) if p.is_file()]))
    write_json(out/'manifest.json',manifest)
    if failure:raise AssertionError(str(failure)+'; '+str(out/'manifest.json'))
    verify(out/'manifest.json');print('Verified slice: '+str(out/'manifest.json'),flush=True)
    return out/'manifest.json'

if __name__=='__main__':run('--browser' in sys.argv)
