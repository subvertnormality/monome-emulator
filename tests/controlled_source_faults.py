"""Unsupported source and invalid injected clock must fail explicitly."""
import argparse,json,sys,uuid
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from automation.client import Session
from automation.protocol import ContractError

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--install',required=True);args=parser.parse_args()
    out=ROOT/'artifacts/c16'/uuid.uuid4().hex;out.mkdir(parents=True);results=[]
    for case in ('duplicate-pulse','unsupported-link'):
        runtime=None;failure=None;caught=None
        try:
            runtime=Session(script=ROOT/'fixtures/probes/controlled-midi-clock/controlled-midi-clock.lua',code_root=ROOT/'fixtures/probes',
                            clock_mode='controlled-experimental',experimental_install=args.install,random_seed=42)
            try:
                if case=='duplicate-pulse':
                    for _ in range(2):runtime.action(dict(type='midi',port=1,bytes=[248]))
                    runtime.action(dict(type='advance',nanoseconds=0))
                else:runtime.action(dict(type='key',n=3,state=1))
                runtime.observe()
            except ContractError as error:caught=str(error)
            assert caught is not None,'Invalid clock source falsely succeeded'
        except Exception as error:failure=dict(type=type(error).__name__,message=str(error))
        finally:
            try:
                if runtime:runtime.close(out/case)
            except ContractError as error:
                # This fault deliberately exercises the native unsupported-source
                # abort. Admit only that exact shutdown; other exits still fail.
                cleanup=json.loads((out/case/'cleanup.json').read_text())
                expected_abort=(case=='unsupported-link' and any(c['service']=='matron' and c['returncode']==-6 for c in cleanup)
                    and all(c['returncode']==0 for c in cleanup if c['service'] not in ('matron','sclang')))
                if not expected_abort:failure=failure or dict(type=type(error).__name__,message=str(error))
            except Exception as error:failure=failure or dict(type=type(error).__name__,message=str(error))
        # Require the native reason; a generic timeout is not accepted evidence.
        if failure is None:
            log=(out/case/'matron.log').read_text(errors='replace')
            wanted='invalid clock reference' if case=='duplicate-pulse' else 'unsupported controlled clock source'
            events=[json.loads(line) for line in (out/case/'native-events.jsonl').read_text().splitlines()]
            if wanted not in log and not any(e.get('kind')==5 and e.get('message')==wanted for e in events):
                failure=dict(type='MissingDiagnostic',message=wanted)
        results.append(dict(case=case,passed=failure is None,failure=failure,caught=caught))
    (out/'manifest.json').write_text(json.dumps(dict(passed=all(r['passed'] for r in results),results=results,status='experimental-not-admitted'),indent=2)+'\n')
    print(out/'manifest.json',flush=True)
    assert all(r['passed'] for r in results),results
if __name__=='__main__':main()
