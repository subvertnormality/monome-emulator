"""Build a clean locked runtime using a verified existing library prefix.

Does not modify shared dependency checkouts, prefix libraries, or current.json.
The reference installation supplies only the prefix; all norns sources are
reconstructed from the current lock and Git objects.
"""
import argparse,hashlib,json,os,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from runtime.dependencies import verify_install,runtime_content,command
from locked_native_source import reconstruct,content_manifest
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--reference-install',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    reference=json.loads(a.reference_install.read_text());prefix=Path(reference['prefix']);library=reference['binaries']['libmonome']
    assert sha(Path(library['path']))==library['sha256'],'Reference library changed'
    assert (prefix/'lib/libmonome.so').resolve()==Path(library['path']).resolve(),'Library outside declared prefix'
    lockpath=ROOT/'dependencies.lock.json';lock=json.loads(lockpath.read_text());a.output=a.output.resolve();a.output.mkdir(parents=True,exist_ok=False)
    source=a.output/'norns';provenance=reconstruct(ROOT,lock,source);provenance['inputs']=content_manifest(source)
    (a.output/'build-inputs.json').write_text(json.dumps(provenance,indent=2)+'\n')
    env=dict(os.environ,CFLAGS='-I'+str(prefix/'include')+' -Wno-error=unused-result',LDFLAGS='-L'+str(prefix/'lib'))
    log=a.output/'build.log';command(['python3','waf','configure','--desktop'],source,log,env);command(['python3','waf','build','--targets=matron,crone','-j8'],source,log,env)
    assert sha(Path(library['path']))==library['sha256'],'Shared library changed during build'
    binaries={name:dict(path=str(path),sha256=sha(path)) for name,path in [('matron',source/'build/matron/matron'),('crone',source/'build/crone/crone'),('libmonome',Path(library['path']))]}
    install=dict(lock_sha256=sha(lockpath),source=str(source),prefix=str(prefix),binaries=binaries,norns_revision=provenance['norns_revision'],patches=lock['patches'],interpreted_files=runtime_content(source),build_inputs_sha256=sha(a.output/'build-inputs.json'))
    (a.output/'installation.json').write_text(json.dumps(install,indent=2)+'\n');verify_install(install);print(a.output/'installation.json')
if __name__=='__main__':main()
