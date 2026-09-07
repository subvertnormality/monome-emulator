"""Compile identical boundary assertions against original and extracted C schedulers."""
import hashlib
import json
import shutil
import subprocess
import sys
import uuid
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from runtime.dependencies import verify_install
sys.path.insert(0,str(ROOT/'scripts'))
from prepare_clock_step import transform


def main():
    current=json.loads((ROOT/'.runtime/current.json').read_text())
    verify_install(current)
    source=Path(current['source'])/'matron/src'
    out=ROOT/'artifacts/c16'/uuid.uuid4().hex;out.mkdir(parents=True)
    candidate=out/'src';shutil.copytree(source,candidate)
    original=(source/'clocks/clock_scheduler.c').read_text()
    (candidate/'clocks/clock_scheduler.c').write_text(transform(original))
    results=[]
    for name,tree in [('baseline',source),('candidate',candidate)]:
        executable=out/name
        command=['cc','-std=gnu11','-Wall','-Wextra','-Werror','-fsanitize=undefined','-g',
                 '-DSCHEDULER_SOURCE="'+str(tree/'clocks/clock_scheduler.c')+'"',
                 str(ROOT/'tests/native_scheduler_step.c'),'-o',str(executable),'-lm','-pthread']
        if name=='candidate':command.insert(1,'-DEXTRACTED_STEP')
        build=subprocess.run(command,capture_output=True,text=True)
        (out/(name+'-build.log')).write_text(build.stdout+build.stderr)
        if build.returncode:raise RuntimeError(build.stderr)
        run=subprocess.run([str(executable)],capture_output=True,text=True,timeout=10)
        (out/(name+'.log')).write_text(run.stdout+run.stderr)
        assert run.returncode==0,(name,run.returncode,run.stdout,run.stderr)
        assert not run.stderr,(name,run.stderr)
        results.append(dict(name=name,output=run.stdout,exit_code=run.returncode,
                            command=command,binary_sha256=hashlib.sha256(executable.read_bytes()).hexdigest()))
    assert results[0]['output']==results[1]['output'],'Native scheduler semantics changed'
    manifest=dict(passed=True,scope='native scheduler boundary only; not controlled-time runtime admission',
                  norns_revision=current['norns_revision'],source_sha256=hashlib.sha256(original.encode()).hexdigest(),
                  runtime_lock_sha256=current['lock_sha256'],
                  candidate_sha256=hashlib.sha256((candidate/'clocks/clock_scheduler.c').read_bytes()).hexdigest(),
                  generator_sha256=hashlib.sha256((ROOT/'scripts/prepare_clock_step.py').read_bytes()).hexdigest(),
                  harness_sha256=hashlib.sha256((ROOT/'tests/native_scheduler_step.c').read_bytes()).hexdigest(),runs=results)
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');print(out/'manifest.json')


if __name__=='__main__':main()
