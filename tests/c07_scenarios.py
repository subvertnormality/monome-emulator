"""Collect and verify C07 native scenarios; repeat seed and beat replay fresh."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from automation import runner,evidence
from automation.protocol import ROOT,write_json

def run():
    names=['native-clock-contract','native-capture-cost','native-seeded-random','native-seeded-random','native-seeded-random',
           'native-beat-replay','native-beat-replay','mosaic-boot']
    records=[]
    try:
        for name in names:
            path,manifest=runner.run(ROOT/'fixtures/scenarios'/(name+'.json'))
            records.append(dict(name=name,manifest=str(path),passed=manifest['passed'],collected=manifest['collected']))
            assert manifest['passed'],manifest['error']
            evidence.verify(path)
            print('Verified '+name+': '+str(path),flush=True)
    finally:write_json(ROOT/'artifacts/c07-scenarios.json',dict(collected=len(records),required=len(names),passed=len(records)==len(names) and all(r['passed'] for r in records),runs=records))

if __name__=='__main__':run()
