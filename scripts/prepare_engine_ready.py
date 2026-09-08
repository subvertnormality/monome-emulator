"""Identify a minimal engine allocation barrier on the pinned official runtime."""
import argparse,difflib,hashlib,json,shutil,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from runtime.dependencies import verify_install,runtime_content

def apply_engine_ready(source):
    path=source/'sc/core/CroneEngine.sc';before=path.read_text()
    marker='\t\t\tthis.alloc;\n\t\t\tdoneCallback.value(this);'
    if before.count(marker)!=1:raise ValueError('Pinned engine allocation boundary changed')
    after=before.replace(marker,'\t\t\tthis.alloc;\n\t\t\tCrone.server.sync;\n\t\t\tdoneCallback.value(this);')
    path.write_text(after)
    return ''.join(difflib.unified_diff(before.splitlines(True),after.splitlines(True),fromfile='a/sc/core/CroneEngine.sc',tofile='b/sc/core/CroneEngine.sc'))

def main():
    p=argparse.ArgumentParser();p.add_argument('--install',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    install=json.loads(a.install.read_text());verify_install(install)
    out=a.output.resolve();out.mkdir(parents=True,exist_ok=False);source=out/'norns';source.mkdir()
    original=Path(install['source'])
    # Only interpreted source changes; all other paths retain their original identity.
    for path in original.iterdir():
        if path.name in ('lua','sc'):shutil.copytree(path,source/path.name)
        else:(source/path.name).symlink_to(path,target_is_directory=path.is_dir())
    patch=apply_engine_ready(source);(out/'engine-ready.patch').write_text(patch)
    install.update(source=str(source),interpreted_files=runtime_content(source))
    install['experimental']['engine_ready_patch_sha256']=hashlib.sha256(patch.encode()).hexdigest()
    verify_install(install);(out/'installation.json').write_text(json.dumps(install,indent=2)+'\n');print(out/'installation.json')
if __name__=='__main__':main()
