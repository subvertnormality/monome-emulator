"""Compare isolated baseline/candidate unit runs; no downloads or user edits."""
import re,shutil,subprocess
from mosaic_candidate import prepare
from automation.protocol import ROOT,uid,read_json,write_json
from automation.identity import artifact

def run():
    candidate=prepare();out=ROOT/'artifacts/c08-unit'/uid();out.mkdir(parents=True)
    runtime=read_json(ROOT/'.runtime/current.json')['source'];records=[]
    for name,source in [('baseline',ROOT/'.runtime/fixtures/mosaic/code/mosaic'),('candidate',candidate/'mosaic')]:
        folder=out/name/'mosaic'
        shutil.copytree(source,folder,ignore=shutil.ignore_patterns('.git','test_artefacts','__pycache__'))
        tests=folder/'lib/tests'
        shutil.copyfile(ROOT/'fixtures/apps/mosaic-patches/memory-preservation-tests.lua',tests/'lib/emulator_memory_regression_tests.lua')
        shutil.copytree(str(runtime)+'/lua',tests/'test_artefacts/norns_test_artefact/lua')
        log=out/(name+'.log')
        with log.open('w') as stream:result=subprocess.run(['lua5.3','run_tests.lua'],cwd=tests,stdout=stream,stderr=subprocess.STDOUT,timeout=90)
        output=log.read_text();match=re.search(r'Ran (\d+) tests in ([\d.]+) seconds, (\d+) successes, (\d+) failures',output)
        assert match,output[-2500:]
        count,seconds,successes,failures=match.groups()
        record=dict(name=name,collected=int(count),seconds=float(seconds),successes=int(successes),failures=int(failures),exit_code=result.returncode,log=artifact(log,ROOT))
        records.append(record);write_json(out/'results.json',dict(runs=records))
        assert int(count)==476,record
        if name=='baseline':
            assert int(failures)==2 and result.returncode!=0,record
            assert 'test_emulator_partial_note_mask_preserves_pattern_on_record_and_redo' in output
            assert 'test_emulator_trig_only_mask_does_not_invent_note_mask' in output
        else:assert int(failures)==0 and int(successes)==476 and result.returncode==0,record
    write_json(out/'results.json',dict(passed=True,runs=records,candidate_manifest=artifact(candidate.parent/'candidate.json',ROOT)))
    print('Verified baseline/candidate unit comparison: '+str(out/'results.json'),flush=True)
    return out/'results.json'

if __name__=='__main__':run()
