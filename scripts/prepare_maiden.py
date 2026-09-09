"""Identify official Maiden assets and its optional BSD WebSocket dependency."""
import argparse,hashlib,json,urllib.request
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
URL='https://files.pythonhosted.org/packages/79/4d/9cc401e7b07e80532ebc8c8e993f42541534da9e9249c59ee0139dcb0352/websockets-12.0-py3-none-any.whl'
SHA='dc284bbc8d7c78a6c69e0c7325ab46ee5e40bb4d50e494d8131a07ef47500e9e'

def main():
    p=argparse.ArgumentParser();p.add_argument('--install',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    value=json.loads(a.install.read_text());lock=json.loads((ROOT/'maiden.lock.json').read_text())
    assert value['official']['revision']==lock['revision'] and value['official']['repository']==lock['repository']
    assert hashlib.sha256(Path(value['binary']).read_bytes()).hexdigest()==value['binary_sha256']
    patch=ROOT/'patches/maiden/0001-follow-directory-links.patch';assert value['patch_sha256']==hashlib.sha256(patch.read_bytes()).hexdigest()
    expected=[dict(path=str(p.relative_to(ROOT)),sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in sorted((ROOT/'patches/maiden').glob('*.patch'))]
    assert value.get('patches')==expected,'Maiden patch set differs'
    out=a.output.resolve();out.mkdir(parents=True,exist_ok=False);wheel=out/URL.split('/')[-1]
    wheel.write_bytes(urllib.request.urlopen(URL,timeout=30).read());assert hashlib.sha256(wheel.read_bytes()).hexdigest()==SHA
    web=Path(value['web']);assert (web/'index.html').is_file()
    value['web_files']=[dict(path=str(p.relative_to(web)),sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in sorted(web.rglob('*')) if p.is_file()]
    value['websocket_dependency']=dict(path=str(wheel),sha256=SHA,url=URL,version='12.0',license='BSD-3-Clause')
    (out/'installation.json').write_text(json.dumps(value,indent=2)+'\n');print(out/'installation.json')
if __name__=='__main__':main()
