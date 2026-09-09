"""Build optional official GPL Maiden separately from the MIT emulator runtime."""
import argparse,base64,hashlib,json,os,platform,subprocess,tarfile,urllib.request,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def extract(archive,destination):
    destination.mkdir(parents=True,exist_ok=True);root=destination.resolve()
    with tarfile.open(archive) as tar:
        for item in tar.getmembers():
            target=(root/item.name).resolve();target.relative_to(root)
            if item.issym():(target.parent/item.linkname).resolve().relative_to(root)
            if item.islnk():(root/item.linkname).resolve().relative_to(root)
            if item.isdev() or item.isfifo():raise ValueError('Unexpected archive special file')
        tar.extractall(root)

def main():
    p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--finalize',action='store_true',help='Record an owned build after manually completing interrupted frontend steps');a=p.parse_args()
    assert platform.system()=='Linux' and platform.machine()=='x86_64','Only the pinned Linux amd64 toolchain is prepared'
    lock=json.loads((ROOT/'maiden.lock.json').read_text());source=a.source.resolve()
    revision=subprocess.check_output(['git','-C',str(source),'rev-parse','HEAD'],text=True).strip();assert revision==lock['revision']
    remote=subprocess.check_output(['git','-C',str(source),'remote','get-url','origin'],text=True).strip();assert remote.rstrip('/')==lock['repository']
    out=a.output.resolve()
    if a.finalize:
        archive=out/'source.tar';tree=out/'source';patch=ROOT/'patches/maiden/0001-follow-directory-links.patch'
        expected=subprocess.check_output(['git','-C',str(source),'archive',revision])
        assert archive.read_bytes()==expected,'Recovery source archive differs from official pin'
        for item in sorted((ROOT/'patches/maiden').glob('*.patch')):
            subprocess.run(['git','apply','--reverse','--check',str(item)],cwd=tree,check=True)
        assert (out/'maiden').read_bytes()[:4]==b'\x7fELF' and (tree/'web/build/index.html').is_file(),'Incomplete build'
        record(out,lock,tree,patch);return
    out.mkdir(parents=True,exist_ok=False)
    archive=out/'source.tar'
    with archive.open('wb') as file:subprocess.run(['git','-C',str(source),'archive',revision],stdout=file,check=True)
    tree=out/'source';extract(archive,tree)
    toolroot=ROOT/'.runtime/maiden-tools';toolroot.mkdir(parents=True,exist_ok=True)
    for tool in lock['tools']:
        archive=toolroot/tool['url'].split('/')[-1]
        if not archive.exists():
            print('Downloading '+tool['name'],flush=True)
            with urllib.request.urlopen(tool['url'],timeout=60) as response,archive.open('wb') as file:
                while True:
                    chunk=response.read(1024*1024)
                    if not chunk:break
                    file.write(chunk)
        data=archive.read_bytes()
        if 'sha256' in tool:assert hashlib.sha256(data).hexdigest()==tool['sha256'],tool['name']
        else:assert base64.b64encode(hashlib.sha512(data).digest()).decode()==tool['sha512_base64'],tool['name']
        destination=toolroot/tool['name']
        if not destination.exists():extract(archive,destination)
    go=toolroot/'go/go';node=toolroot/'node/node-v16.20.2-linux-x64';yarn=toolroot/'yarn/package/bin/yarn.js'
    env=dict(os.environ,GOROOT=str(go),GOPATH=str(toolroot/'gopath'),GOCACHE=str(toolroot/'go-cache'),
        PATH=str(go/'bin')+':'+str(node/'bin')+':'+os.environ['PATH'],YARN_CACHE_FOLDER=str(toolroot/'yarn-cache'),CI='true')
    patch=ROOT/'patches/maiden/0001-follow-directory-links.patch'
    for item in sorted((ROOT/'patches/maiden').glob('*.patch')):
        subprocess.run(['git','apply',str(item)],cwd=tree,check=True)
    with (out/'build.log').open('w') as log:
        subprocess.run([str(go/'bin/go'),'build','-mod=readonly','-o',str(out/'maiden')],cwd=tree,env=env,stdout=log,stderr=log,check=True,timeout=600)
        print('Go binary built; installing pinned frontend dependencies',flush=True)
        subprocess.run([str(node/'bin/node'),str(yarn),'install','--frozen-lockfile','--non-interactive','--network-concurrency','1','--network-timeout','60000'],cwd=tree/'web',env=env,stdout=log,stderr=log,check=True,timeout=1800)
        # The archive has no .git: stamp the exact pin instead of querying a parent repository.
        (tree/'web/src/version.js').write_text("export const VERSION = '0.5.0';\nexport const COMMIT = '"+revision+"';\n")
        subprocess.run([str(node/'bin/node'),'node_modules/react-scripts/scripts/build.js'],cwd=tree/'web',env=env,stdout=log,stderr=log,check=True,timeout=300)
    record(out,lock,tree,patch)

def record(out,lock,tree,patch):
    # Ace loads these workers at runtime; webpack does not discover their URLs.
    for language in ('lua','json'):
        worker='worker-'+language+'.js'
        shutil.copyfile(tree/'web/node_modules/ace-builds/src-min-noconflict'/worker,tree/'web/build/static/js'/worker)
    result=dict(schema_version=1,official=lock,source=str(tree),binary=str(out/'maiden'),binary_sha256=hashlib.sha256((out/'maiden').read_bytes()).hexdigest(),
        web=str(tree/'web/build'),license=str(tree/'LICENSE'),patch_sha256=hashlib.sha256(patch.read_bytes()).hexdigest() if patch.exists() else None)
    result['patches']=[dict(path=str(p.relative_to(ROOT)),sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in sorted((ROOT/'patches/maiden').glob('*.patch'))]
    (out/'installation.json').write_text(json.dumps(result,indent=2)+'\n');print(out/'installation.json',flush=True)
if __name__=='__main__':main()
