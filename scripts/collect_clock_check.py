"""Run one required real-time/fault package and bind its native evidence for M5."""
import argparse,hashlib,json,platform,subprocess,sys,time,unittest,uuid
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'src'),str(ROOT/'tests')]
from automation.identity import artifact,source_identity
from automation.protocol import read_json
from automation.clock_admission import generic_check

def ref(path):return dict(path=str(path),sha256=hashlib.sha256(path.read_bytes()).hexdigest())

def main():
    specs=read_json(ROOT/'compatibility/controlled-admission.json')['generic_checks']
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--check',choices=specs,required=True)
    parser.add_argument('--install',type=Path,required=True);args=parser.parse_args()
    out=ROOT/'artifacts/c16'/('check-'+uuid.uuid4().hex);out.mkdir(parents=True)
    spec=specs[args.check];source=source_identity();candidate=read_json(args.install);default=read_json(ROOT/'.runtime/current.json')
    record=dict(kind='native-clock-check',id=args.check,source=source,profile='wsl' if 'microsoft' in platform.release().lower() else 'linux',
        host=dict(release=platform.release(),platform=platform.platform()),passed=False,exit_code=1,phases={},failure=None)
    started=time.monotonic()
    try:
        if args.check.startswith('realtime-clocks'):
            import clock_native
            from automation import session
            before=set((ROOT/'artifacts/c07').glob('*/*/identity.json'))
            original=session.start
            def selected_start(*a,**kw):
                if spec['runtime']=='candidate':kw['experimental_install']=str(args.install.resolve())
                return original(*a,**kw)
            # Select only the public installation argument. Native clocks,
            # callback dispatch, input/output and test assertions run unchanged.
            with (out/'command.log').open('w') as stream,patch.object(session,'start',selected_start):
                suite=unittest.defaultTestLoader.loadTestsFromTestCase(clock_native.NativeClocks)
                result=unittest.TextTestRunner(stream=stream,verbosity=2).run(suite)
            result_path=out/'result.json'
            result_path.write_text(json.dumps(dict(passed=result.wasSuccessful(),tests_run=result.testsRun,
                failures=len(result.failures),errors=len(result.errors),skipped=len(result.skipped)),indent=2)+'\n')
            assert result.wasSuccessful() and result.testsRun==3 and not result.skipped,'Real-time clock tests failed or skipped'
            names={'clock-contract':'clock-contract','reset-anchor':'reset-anchor','scheduled-input':'future-midi'}
            discovered=set((ROOT/'artifacts/c07').glob('*/*/identity.json'))-before
            assert len(discovered)==3,'Missing or concurrent clock-test phase output'
            for path in discovered:
                directory=path.parent;role=names[directory.parent.name]
                assert role not in record['phases'],'Duplicate clock role'
                record['phases'][role]=dict(directory=str(directory),artifacts=[artifact(p,directory) for p in sorted(directory.rglob('*')) if p.is_file()])
        else:
            if args.check.startswith('wall-'):
                command=[sys.executable,str(ROOT/'tests/controlled_wall_timer_native.py'),'--real-time']
            elif args.check.startswith('transition-'):
                command=[sys.executable,str(ROOT/'tests/transition_realtime_native.py')]
            else:command=[sys.executable,str(ROOT/'tests/controlled_source_faults.py')]
            if spec['runtime']=='candidate':command+=['--install',str(args.install.resolve())]
            result=subprocess.run(command,cwd=ROOT,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
            (out/'command.log').write_text(result.stdout)
            assert result.returncode==0,'Native check failed; see command.log'
            result_path=Path(result.stdout.strip().splitlines()[-1]).resolve()
            result_path.relative_to(ROOT/'artifacts/c16')
            for role in spec['phases']:
                directory=result_path.parent/role
                record['phases'][role]=dict(directory=str(directory),artifacts=[artifact(p,directory) for p in sorted(directory.rglob('*')) if p.is_file()])
        record['result']=ref(result_path)
        assert source_identity()['digest']==source['digest'],'Sources changed while native checks ran'
        record.update(passed=True,exit_code=0)
        (out/'manifest.json').write_text(json.dumps(record,indent=2)+'\n')
        generic_check(out/'manifest.json',args.check,spec,source['digest'],candidate,default,record['profile'])
    except Exception as error:record.update(passed=False,exit_code=1,failure=dict(type=type(error).__name__,message=str(error)))
    finally:
        record['wall_elapsed_seconds']=time.monotonic()-started
        (out/'manifest.json').write_text(json.dumps(record,indent=2)+'\n');print(out/'manifest.json',flush=True)
    if not record['passed']:raise SystemExit(1)
if __name__=='__main__':main()
