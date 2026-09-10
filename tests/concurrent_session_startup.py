"""Start several native sessions at the same instant and count startup failures.

Generic reliability probe (no application code): each session loads the
performance-clock probe and must reach a first snapshot. Records every failure
with its code and log directory. Usage:
    PYTHONPATH=src python3 tests/concurrent_session_startup.py --sessions 6 --trials 3 --output DIR
"""
import argparse,json,sys,tempfile,threading,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from automation.client import Session
from automation.protocol import ContractError,write_json

def start_one(barrier,results,index,data_root,output):
    barrier.wait()
    started=time.monotonic();session=None
    try:
        session=Session(script=ROOT/'fixtures/probes/performance-clock/performance-clock.lua',
                        code_root=ROOT/'fixtures/probes',data=data_root/str(index),crow_enabled=False)
        session.observe()
        results[index]=dict(passed=True,seconds=round(time.monotonic()-started,2),session_id=session.id)
    except Exception as error:
        results[index]=dict(passed=False,seconds=round(time.monotonic()-started,2),
                            code=getattr(error,'code',type(error).__name__),message=str(error)[:400])
    finally:
        if session:
            try:session.close(output/('session-%d-%s'%(index,session.id)))
            except Exception as error:results[index]['close_error']=str(error)[:300]

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--sessions',type=int,default=6)
    parser.add_argument('--trials',type=int,default=3);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();args.output.mkdir(parents=True,exist_ok=False)
    trials=[]
    for trial in range(args.trials):
        with tempfile.TemporaryDirectory() as data:
            barrier=threading.Barrier(args.sessions);results=[None]*args.sessions
            threads=[threading.Thread(target=start_one,args=(barrier,results,i,Path(data),args.output/('trial-%d'%(trial+1)))) for i in range(args.sessions)]
            for t in threads:t.start()
            for t in threads:t.join()
        trials.append(dict(trial=trial+1,failures=sum(not r['passed'] for r in results),results=results))
        print(json.dumps(dict(trial=trial+1,failures=trials[-1]['failures'])),flush=True)
    report=dict(schema_version=1,sessions=args.sessions,trials=trials,
                total_failures=sum(t['failures'] for t in trials),passed=all(t['failures']==0 for t in trials))
    write_json(args.output/'result.json',report)
    return 0 if report['passed'] else 1

if __name__=='__main__':raise SystemExit(main())
