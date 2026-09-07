"""Native metro loop/external-step comparison; boundary evidence, not D admission."""
import hashlib,json,shutil,subprocess,sys,uuid
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'));sys.path.insert(0,str(ROOT/'scripts'))
from runtime.dependencies import verify_install
from prepare_metro_step import transform,transform_header

def main():
    current=json.loads((ROOT/'.runtime/current.json').read_text());verify_install(current)
    source=Path(current['source'])/'matron/src';out=ROOT/'artifacts/c16'/uuid.uuid4().hex;out.mkdir(parents=True)
    candidate=out/'src';shutil.copytree(source,candidate)
    before=(source/'metro.c').read_text();(candidate/'metro.c').write_text(transform(before))
    (candidate/'metro.h').write_text(transform_header((candidate/'metro.h').read_text()))
    rows=[]
    for name,tree in [('baseline',source),('candidate-native',candidate),('candidate',candidate)]:
        binary=out/name
        command=['cc','-std=gnu11','-Wall','-Wextra','-Werror','-fsanitize=undefined','-g',
                 '-DMETRO_SOURCE="'+str(tree/'metro.c')+'"',str(ROOT/'tests/native_metro_step.c'),'-o',str(binary),'-pthread']
        if name=='candidate':command.insert(1,'-DEXTRACTED_STEP')
        build=subprocess.run(command,capture_output=True,text=True);(out/(name+'-build.log')).write_text(build.stdout+build.stderr)
        assert build.returncode==0,build.stderr
        run=subprocess.run([str(binary)],capture_output=True,text=True,timeout=10);(out/(name+'.log')).write_text(run.stdout+run.stderr)
        assert run.returncode==0 and not run.stderr,(run.returncode,run.stdout,run.stderr)
        rows.append(dict(name=name,output=run.stdout,command=command,exit_code=run.returncode,binary_sha256=hashlib.sha256(binary.read_bytes()).hexdigest()))
    assert all(row['output']==rows[0]['output'] for row in rows),'Metro semantics changed'
    result=dict(passed=True,scope='native metro boundary; not D admission',runtime_lock_sha256=current['lock_sha256'],
                source_sha256=hashlib.sha256(before.encode()).hexdigest(),candidate_sha256=hashlib.sha256((candidate/'metro.c').read_bytes()).hexdigest(),runs=rows)
    (out/'manifest.json').write_text(json.dumps(result,indent=2)+'\n');print(out/'manifest.json')
if __name__=='__main__':main()
