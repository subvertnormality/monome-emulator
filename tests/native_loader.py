"""C02 actual-runtime suite. No application globals are used as workflow oracles."""
import json
from pathlib import Path
import sys
import time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from automation import session,runner,evidence
from automation.protocol import ROOT,ContractError,write_json
from automation.identity import source_identity
from native_smoke import smoke

records=[]
def record(name,**extra):
    records.append(dict(name=name,passed=True,**extra)); print('PASS '+name,flush=True)

def scenarios():
    for name in ('native-probe-a','native-probe-b','mosaic-boot','mosaic-mod-boot'):
        path,value=runner.run(ROOT/'fixtures/scenarios'/(name+'.json'))
        assert value['passed'],value['error']
        cleanup=json.loads((path.parent/'cleanup.json').read_text())
        assert all(c['returncode']==0 for c in cleanup if c['service'] in ('matron','crone','jack')),cleanup
        evidence.verify(path)
        observations=json.loads((path.parent/'observations.json').read_text())
        observed=observations[-1]
        if name.startswith('mosaic'):
            d=observed['state']['diagnostics']
            # Mosaic uses live scheduler/redraw coroutines. Its stopped initial
            # autosave metro is armed by subsequent editing, not unconditional init.
            assert d['clock_threads']>=4,d
            assert observed['frame_revision']>1 and len(set((path.parent/'frame.bgra').read_bytes()))>1
            log=(path.parent/'matron.log').read_text()
            assert 'loaded keyboard layout: us' in log
            if name=='mosaic-mod-boot':
                for hook in ('toolkit pre init','aa metrix mod depth params','~ matrix one last param read'):
                    assert 'calling: '+hook in log,hook
        record(name,manifest=str(path),session_id=value['session_id'])

def failures():
    for app,expected in [('error-init','intentional'),('error-coroutine','intentional native coroutine failure'),('error-hook','intentional hook failure')]:
        recipe=dict(schema_version=1,id='G02-'+app,backend='native',script='fixtures/probes/'+app+'/'+app+'.lua',
            code_root='fixtures/probes',tier='F',family='G02',deadline_ms=60000,
            steps=[dict(wait=dict(path='state.script',equals='never-ready'),timeout_ms=3000)])
        path=ROOT/'artifacts/c02'/('scenario-'+app+'.json'); write_json(path,recipe)
        manifest,value=runner.run(path)
        assert not value['passed'] and value['exit_code']==1,value
        assert value['error']['code']=='lua_error' and expected in value['error']['message'],value['error']
        assert (manifest.parent/'matron.log').is_file()
        assert expected in (manifest.parent/'matron.log').read_text()
        record(app,manifest=str(manifest),error=value['error'],session_id=value['session_id'])

def isolation():
    first=session.start('native',ROOT/'fixtures/probes/probe-a/probe-a.lua',ROOT/'fixtures/probes')
    second=None
    try:
        second=session.start('native',ROOT/'fixtures/probes/probe-b/probe-b.lua',ROOT/'fixtures/probes')
        for key in ('session_id','dust','data','port','pid'): assert first[key]!=second[key],key
        a=session.request(first['session_id'],'/snapshot'); b=session.request(second['session_id'],'/snapshot')
        assert a['state']['script']=='probe-a' and b['state']['script']=='probe-b'
        assert a['state']['midi_count']==3 and b['state']['midi_count']==0
        smoke(second); second=None
        assert session.request(first['session_id'],'/snapshot')['state']['script']=='probe-a'
        record('concurrent-isolation-and-native-smoke',first=first['session_id'])
    finally:
        if second: session.stop(second['session_id'])
        session.stop(first['session_id'])

def no_survivors():
    # Each owned service uses the unique session HOME. Inspect only sessions in
    # this suite; unrelated user processes are never killed or claimed as ours.
    sessions={p.name for p in session.SESSIONS.iterdir() if (p/'config.json').exists()}-baseline
    leaked=[]
    for process in Path('/proc').iterdir():
        if not process.name.isdigit(): continue
        try: environment=(process/'environ').read_bytes()
        except (OSError,PermissionError): continue
        if any(('HOME=/tmp/norns_emu_'+sid+'\0').encode() in environment for sid in sessions): leaked.append(process.name)
    assert not leaked,leaked
    assert not any((Path('/tmp')/('norns_emu_'+sid)).exists() for sid in sessions)
    record('owned-services-and-aliases-cleaned',sessions=sorted(sessions))

if __name__=='__main__':
    baseline={p.name for p in session.SESSIONS.iterdir()}; identity=source_identity()
    try:
        scenarios(); failures(); isolation(); no_survivors()
        assert identity['digest']==source_identity()['digest'],'Source changed during suite'
        write_json(ROOT/'artifacts/c02/loader-suite.json',dict(passed=True,source=identity,collected=len(records),results=records))
    except Exception as error:
        write_json(ROOT/'artifacts/c02/loader-suite.json',dict(passed=False,source=identity,collected=len(records),results=records,error=repr(error)))
        raise
