"""Exercise actual host trace exhaustion, exclusive creation and fresh restarts."""
import argparse,hashlib,json,os,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from automation.identity import source_identity

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--build',type=Path,required=True);args=parser.parse_args()
    build=args.build.resolve();manifest=json.loads((build/'manifest.json').read_text())
    binary=build/'crow-host';assert hashlib.sha256(binary.read_bytes()).hexdigest()==manifest['binary_sha256']
    out=ROOT/'artifacts/crow'/time.strftime('ii-limits-%Y%m%d-%H%M%S');out.mkdir(parents=True)
    report=dict(passed=False,build=manifest,source=source_identity(),checks=[])
    command=[str(binary),manifest['source'],manifest['serial_path'],'--serial']
    def run(name,payload,path=None):
        path=path or out/(name+'.jsonl');env=dict(os.environ,NORNS_EMU_CROW_II_TRACE=str(path))
        for key in ('NORNS_EMU_CROW_CAPTURE_FD','NORNS_EMU_CROW_CAPTURE_DIRECTORY'):env.pop(key,None)
        result=subprocess.run(command,input=payload,capture_output=True,env=env,timeout=90)
        (out/(name+'.stderr')).write_bytes(result.stderr)
        return result,path
    try:
        result,path=run('limit',b'ii.jf.mode(1)\n'*100001)
        assert result.returncode==1 and b'trace packet limit reached' in result.stderr,result.stderr
        rows=[json.loads(line) for line in path.read_text().splitlines()]
        assert len(rows)==100000 and [r['sequence'] for r in rows]==list(range(1,100001))
        assert all(r['address']==112 and r['bytes']==[6,1] for r in rows)
        digest=hashlib.sha256(path.read_bytes()).hexdigest()
        report['checks'].append(dict(name='100000-packets-retained-next-fails',sha256=digest))
        result,_=run('exclusive',b'ii.jf.mode(0)\n',path)
        assert result.returncode==1 and b'trace unavailable' in result.stderr
        assert hashlib.sha256(path.read_bytes()).hexdigest()==digest
        report['checks'].append(dict(name='existing-trace-not-overwritten',passed=True))
        for name,mode in [('restart-a',0),('restart-b',1)]:
            result,fresh=run(name,('ii.jf.mode(%d)\n'%mode).encode())
            assert result.returncode==0,result.stderr
            records=[json.loads(line) for line in fresh.read_text().splitlines()]
            assert len(records)==1 and records[0]['sequence']==1 and records[0]['bytes']==[6,mode]
        report['checks'].append(dict(name='fresh-hosts-reset-sequence-and-isolate-traces',passed=True))
        report['passed']=True
    except Exception as error:report['error']=repr(error);raise
    finally:(out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(out,flush=True)
if __name__=='__main__':main()
