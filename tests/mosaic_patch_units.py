"""Supplementary unchanged upstream tests against explicit isolated candidates."""
import re,shutil,subprocess,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tests'))
from mosaic_candidate import prepare
from automation.protocol import ROOT,uid,read_json,write_json
from automation.identity import artifact


def run(spec):
    candidate=prepare(ROOT/spec);out=ROOT/'artifacts/c08-patch-unit'/uid();out.mkdir(parents=True)
    runtime=Path(read_json(ROOT/'.runtime/current.json')['source']);records=[]
    for name,source in [('baseline',ROOT/'.runtime/fixtures/mosaic/code/mosaic'),('candidate',candidate/'mosaic')]:
        folder=out/name/'mosaic'
        shutil.copytree(source,folder,ignore=shutil.ignore_patterns('.git','test_artefacts','__pycache__'))
        tests=folder/'lib/tests';shutil.copytree(runtime/'lua',tests/'test_artefacts/norns_test_artefact/lua')
        log=out/(name+'.log')
        with log.open('w') as stream:result=subprocess.run(['lua5.3','run_tests.lua'],cwd=tests,stdout=stream,stderr=subprocess.STDOUT,timeout=90)
        output=log.read_text();match=re.search(r'Ran (\d+) tests in ([\d.]+) seconds, (\d+) successes, (\d+) failures?',output)
        assert match,output[-2500:]
        count,seconds,successes,failures=match.groups()
        records.append(dict(name=name,collected=int(count),seconds=float(seconds),successes=int(successes),failures=int(failures),exit_code=result.returncode,log=artifact(log,ROOT)))
        write_json(out/'results.json',dict(runs=records,candidate_manifest=artifact(candidate.parent/'candidate.json',ROOT)))
        assert int(count)==474,records[-1]
    passed=all(r['exit_code']==0 and r['failures']==0 and r['successes']==474 for r in records)
    write_json(out/'results.json',dict(passed=passed,runs=records,candidate_manifest=artifact(candidate.parent/'candidate.json',ROOT)))
    print(str(out/'results.json'),flush=True)
    assert passed,records

if __name__=='__main__':run(sys.argv[1])
