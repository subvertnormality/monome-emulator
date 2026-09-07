"""Run required generic scheduled-input phases and verify their native evidence."""
import argparse,json,platform,subprocess,sys,time,uuid
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from automation.identity import artifact,source_identity
from automation.protocol import read_json,write_json
from automation.clock_admission import generic_check
from runtime.dependencies import verify_install


def main():
    specs=read_json(ROOT/'compatibility/controlled-admission.json')['generic_checks']
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check',choices=[k for k,v in specs.items() if v.get('kind')=='midi-schedule'],required=True)
    parser.add_argument('--install',type=Path,required=True)
    args=parser.parse_args();spec=specs[args.check]
    out=ROOT/'artifacts/c16'/('queue-check-'+uuid.uuid4().hex);out.mkdir()
    source=source_identity();candidate=read_json(args.install);default=read_json(ROOT/'.runtime/current.json')
    verify_install(candidate)
    if spec['runtime']=='default' and candidate!=default:parser.error('Default check must select the actual default installation')
    record=dict(kind='native-clock-check',id=args.check,source=source,profile='wsl' if 'microsoft' in platform.release().lower() else 'linux',
        host=dict(release=platform.release(),platform=platform.platform()),passed=False,exit_code=1,phases={},failure=None)
    started=time.monotonic()
    try:
        for role in spec['phases']:
            directory=out/role
            script='probe_logical_midi.py' if spec['mode']=='controlled-experimental' else 'probe_scheduled_midi.py'
            result=subprocess.run([sys.executable,str(ROOT/'scripts'/script),'--installation',str(args.install.resolve()),
                '--output',str(directory)],cwd=ROOT,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
            (out/(role+'.log')).write_text(result.stdout)
            record['phases'][role]=dict(directory=role,artifacts=[artifact(p,directory) for p in sorted(directory.rglob('*')) if p.is_file()])
            if result.returncode:raise RuntimeError('Queue phase failed: '+role)
        if source_identity()['digest']!=source['digest']:raise RuntimeError('Sources changed during queue checks')
        record.update(passed=True,exit_code=0)
        write_json(out/'manifest.json',record)
        generic_check(out/'manifest.json',args.check,spec,source['digest'],candidate,default,record['profile'])
    except Exception as error:record.update(passed=False,exit_code=1,failure=dict(type=type(error).__name__,message=str(error)))
    finally:
        record['wall_elapsed_seconds']=time.monotonic()-started
        write_json(out/'manifest.json',record);print(out/'manifest.json',flush=True)
    return record['exit_code']


if __name__=='__main__':raise SystemExit(main())
