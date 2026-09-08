"""Prove pinned input/detection behavior before native injection integration."""
import argparse,hashlib,json,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from automation.identity import source_identity

def main():
    p=argparse.ArgumentParser();p.add_argument('--build',type=Path,required=True);a=p.parse_args()
    build=a.build.resolve();manifest=json.loads((build/'manifest.json').read_text())
    assert hashlib.sha256((build/'crow-host').read_bytes()).hexdigest()==manifest['binary_sha256']
    for name,digest in manifest['portable_sources'].items():
        assert hashlib.sha256((build/'core'/name).read_bytes()).hexdigest()==digest
        assert hashlib.sha256((Path(manifest['source'])/'lib'/name).read_bytes()).hexdigest()==digest
    out=ROOT/'artifacts/crow'/time.strftime('input-core-%Y%m%d-%H%M%S');out.mkdir(parents=True)
    report=dict(passed=False,build=manifest,source=source_identity())
    try:
        result=subprocess.run([str(build/'crow-host'),manifest['source'],str(ROOT/'tests/crow_input_core.lua')],capture_output=True,text=True,timeout=5)
        (out/'stdout.log').write_text(result.stdout);(out/'stderr.log').write_text(result.stderr)
        assert result.returncode==0,result.stderr
        report['metrics']=json.loads(result.stdout.strip().splitlines()[-1])
        assert report['metrics']['passed'] and report['metrics']['checks']==5
        report['passed']=True
    except Exception as error:report['error']=repr(error);raise
    finally:(out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(out)
if __name__=='__main__':main()
