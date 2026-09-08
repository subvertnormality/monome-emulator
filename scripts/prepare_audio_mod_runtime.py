"""Create an identified SC-only candidate, reusing unchanged native binaries."""
import argparse, difflib, hashlib, json, shutil, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from runtime.dependencies import verify_install, runtime_content

def apply_default_server(source):
    path=source/'sc/core/Crone.sc';before=path.read_text()
    marker='\t\t\tserverPort = server.addr.port;'
    if before.count(marker)!=1 or '\t\t\tServer.default = server;' in before:
        raise ValueError('Pinned Crone startup changed or default-server patch already present')
    after=before.replace(marker,'\t\t\tServer.default = server;\n'+marker)
    path.write_text(after)
    return ''.join(difflib.unified_diff(before.splitlines(True),after.splitlines(True),fromfile='a/sc/core/Crone.sc',tofile='b/sc/core/Crone.sc'))

def main():
    p=argparse.ArgumentParser();p.add_argument('--install',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    install=json.loads(a.install.read_text());verify_install(install)
    if install.get('experimental',{}).get('status')!='audio-feasibility-only':raise ValueError('Requires experimental audio installation')
    out=a.output.resolve();out.mkdir(parents=True,exist_ok=False)
    original=Path(install['source']);source=out/'norns'
    shutil.copytree(original,source,ignore=shutil.ignore_patterns('.git','build'))
    (source/'build').symlink_to(original/'build',target_is_directory=True)
    patch=apply_default_server(source)
    (out/'default-server.patch').write_text(patch)
    install.update(source=str(source),interpreted_files=runtime_content(source))
    install['experimental']['default_server_patch_sha256']=hashlib.sha256(patch.encode()).hexdigest()
    (out/'installation.json').write_text(json.dumps(install,indent=2)+'\n');verify_install(install)
    print(out/'installation.json')
if __name__=='__main__':main()
