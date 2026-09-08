"""Unchanged, opt-in cheat codes 2 boot diagnosis; not workflow acceptance."""
import argparse, hashlib, json, shutil, subprocess, sys, time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from automation import session
from automation.identity import application_identity
from automation.protocol import write_json

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--install',type=Path,required=True)
    args=parser.parse_args()
    code=ROOT/'.runtime/fixtures/cheat-codes-2/code'; app=code/'cheat_codes_2'
    lock=json.loads((ROOT/'fixtures/apps/cheat-codes-2.lock.json').read_text())
    def git(path,*args): return subprocess.check_output(['git','-C',str(path),*args],text=True).strip()
    assert git(app,'rev-parse','HEAD')==lock['application']['commit']
    assert not git(app,'status','--porcelain'), 'Fixture has local changes; preserving it'
    for sub in lock['application']['submodules']:
        assert git(app/sub['path'],'rev-parse','HEAD')==sub['commit']
        assert not git(app/sub['path'],'status','--porcelain')
    out=ROOT/'artifacts/audio'/('cheat-codes-boot-'+time.strftime('%Y%m%d-%H%M%S'));out.mkdir(parents=True)
    before=application_identity(code)
    report=dict(passed=False,scope='unchanged boot and input responsiveness only',fixture=lock,application=before,
        install=json.loads(args.install.read_text()),
        version_limitation='Launcher writes synthetic host update 260906. This does not establish official OS release compatibility. Runtime is pinned official norns v2.9.4, commit dated 2026-01-02. No fixture version guard was edited.')
    sid=None
    try:
        info=session.start('native',app/'cheat_codes_2.lua',code,experimental_install=args.install)
        sid=info['session_id'];report['session_id']=sid
        time.sleep(3)
        initial=session.request(sid,'/snapshot');report['initial']=initial
        assert initial['state']['script']=='cheat_codes_2', 'Loaded fallback script'
        from audio_feasibility import key
        key(sid,2)
        time.sleep(.3)
        report['after_key']=session.request(sid,'/snapshot')
        assert report['after_key']['frame_revision']>initial['frame_revision'], 'No frame update after real key'
        report['passed']=True
    except Exception as error:
        report['error']=repr(error)
        if getattr(error,'session_id',None):report['session_id']=error.session_id
        raise
    finally:
        if sid:session.stop(sid)
        if report.get('session_id'):
            directory=session.SESSIONS/report['session_id']
            for name in ('matron.log','sclang.log','crone.log','jack.log','native-config.json','native-events.jsonl','cleanup.json','startup-error.json'):
                if (directory/name).exists():shutil.copyfile(directory/name,out/name)
        report['source_unchanged']=application_identity(code)==before
        report['artifacts']=[dict(path=p.name,sha256=hashlib.sha256(p.read_bytes()).hexdigest(),size=p.stat().st_size) for p in out.iterdir() if p.is_file()]
        write_json(out/'report.json',report);print(out/'report.json',flush=True)
        assert report['source_unchanged'],'Application source changed'

if __name__=='__main__':main()
