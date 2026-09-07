"""Build an opt-in native candidate without changing the current installation."""
import argparse,hashlib,json,os,shutil,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from runtime.dependencies import verify_install,runtime_content,command

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--candidate',type=Path,required=True);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();args.output=args.output.resolve();args.output.mkdir(parents=True,exist_ok=False)
    base=json.loads((ROOT/'.runtime/current.json').read_text());verify_install(base)
    source=args.output/'norns';prefix=Path(base['prefix']);log=args.output/'build.log'
    shutil.copytree(base['source'],source,ignore=shutil.ignore_patterns('.git','build','.waf-*','.lock-waf*','__pycache__'))
    patch=args.candidate.resolve()/'controlled-runtime.patch';manifest=json.loads((args.candidate/'candidate.json').read_text())
    assert hashlib.sha256(patch.read_bytes()).hexdigest()==manifest['patch_sha256']
    env=dict(os.environ,GIT_CEILING_DIRECTORIES=str(source.parent),CFLAGS='-I'+str(prefix/'include')+' -Wno-error=unused-result',LDFLAGS='-L'+str(prefix/'lib'))
    command(['git','apply','--check',str(patch)],source,log,env);command(['git','apply',str(patch)],source,log,env)
    for item in manifest['files']:
        assert hashlib.sha256((source/item['path']).read_bytes()).hexdigest()==item['after_sha256'],item['path']
    command(['python3','waf','configure','--desktop'],source,log,env)
    command(['python3','waf','build','--targets=matron,crone','-j8'],source,log,env)
    binaries={}
    for name,path in [('matron',source/'build/matron/matron'),('crone',source/'build/crone/crone'),('libmonome',prefix/'lib/libmonome.so')]:
        binaries[name]=dict(path=str(path),sha256=hashlib.sha256(path.read_bytes()).hexdigest())
    install=dict(base,source=str(source),binaries=binaries,interpreted_files=runtime_content(source),experimental=manifest)
    (args.output/'installation.json').write_text(json.dumps(install,indent=2)+'\n')
    verify_install(install);print(args.output/'installation.json')
if __name__=='__main__':main()
