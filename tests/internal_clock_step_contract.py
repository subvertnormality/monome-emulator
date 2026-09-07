"""Compare original/native internal-clock loop and external publication seam."""
import hashlib,json,shutil,subprocess,sys,uuid
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'));sys.path.insert(0,str(ROOT/'scripts'))
from runtime.dependencies import verify_install
from prepare_internal_clock_step import transform,transform_header

def main():
    current=json.loads((ROOT/'.runtime/current.json').read_text());verify_install(current)
    source=Path(current['source'])/'matron/src'
    out=ROOT/'artifacts/c16'/uuid.uuid4().hex;out.mkdir(parents=True)
    candidate=out/'src';shutil.copytree(source,candidate)
    before=(source/'clocks/clock_internal.c').read_text()
    (candidate/'clocks/clock_internal.c').write_text(transform(before))
    header=candidate/'clocks/clock_internal.h';header.write_text(transform_header(header.read_text()))
    rows=[]
    for name,tree in [('baseline',source),('candidate',candidate)]:
        binary=out/name
        command=['cc','-std=gnu11','-Wall','-Wextra','-Werror','-fsanitize=undefined','-g',
                 '-I'+str(tree),'-DINTERNAL_SOURCE="'+str(tree/'clocks/clock_internal.c')+'"',
                 str(ROOT/'tests/native_internal_clock_step.c'),'-o',str(binary),'-lm','-pthread']
        if name=='candidate':command.insert(1,'-DEXTRACTED_STEP')
        build=subprocess.run(command,capture_output=True,text=True)
        (out/(name+'-build.log')).write_text(build.stdout+build.stderr)
        assert build.returncode==0,build.stderr
        run=subprocess.run([str(binary)],capture_output=True,text=True,timeout=10)
        (out/(name+'.log')).write_text(run.stdout+run.stderr)
        assert run.returncode==0 and not run.stderr,(run.returncode,run.stdout,run.stderr)
        rows.append(dict(name=name,output=run.stdout,command=command,exit_code=run.returncode,
                         binary_sha256=hashlib.sha256(binary.read_bytes()).hexdigest()))
    assert rows[0]['output']==rows[1]['output'],'Internal-clock semantics changed'
    result=dict(passed=True,scope='native internal-clock boundary; not D admission',runtime_lock_sha256=current['lock_sha256'],
                source_sha256=hashlib.sha256(before.encode()).hexdigest(),candidate_sha256=hashlib.sha256((candidate/'clocks/clock_internal.c').read_bytes()).hexdigest(),runs=rows)
    (out/'manifest.json').write_text(json.dumps(result,indent=2)+'\n');print(out/'manifest.json')
if __name__=='__main__':main()
