"""Record actual Crow core feasibility and explicit Lua failure propagation."""
import argparse, hashlib, json, subprocess, sys, time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from automation.identity import source_identity
def main():
    p=argparse.ArgumentParser();p.add_argument('--build',type=Path,required=True);a=p.parse_args()
    build=a.build.resolve();manifest=json.loads((build/'manifest.json').read_text());binary=build/'crow-host'
    assert hashlib.sha256(binary.read_bytes()).hexdigest()==manifest['binary_sha256']
    out=ROOT/'artifacts/crow'/time.strftime('core-%Y%m%d-%H%M%S');out.mkdir(parents=True)
    report=dict(passed=False,build=manifest,emulator=source_identity(),checks=[])
    try:
        result=subprocess.run([str(binary),manifest['source'],str(ROOT/'tests/crow_core.lua')],capture_output=True,text=True,timeout=10)
        (out/'core.stdout').write_text(result.stdout);(out/'core.stderr').write_text(result.stderr)
        assert result.returncode==0,result.stderr
        metrics=json.loads(result.stdout.strip().splitlines()[-1]);assert metrics['passed'] and metrics['checks']==5
        report['checks'].append(dict(name='official-crow-cv-core',metrics=metrics))
        bad=out/'bad.lua';bad.write_text('error("intentional crow script failure")\n')
        result=subprocess.run([str(binary),manifest['source'],str(bad)],capture_output=True,text=True,timeout=5)
        assert result.returncode!=0 and 'intentional crow script failure' in result.stderr
        (out/'failure.stderr').write_text(result.stderr);report['checks'].append(dict(name='lua-error-propagates',passed=True))
        report['passed']=True
    except Exception as error:report['error']=repr(error);raise
    finally:(out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(out)
if __name__=='__main__':main()
