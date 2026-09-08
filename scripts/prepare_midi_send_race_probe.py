"""Isolated test-only scheduling seam; never promote this candidate."""
import argparse,difflib,hashlib,json
from pathlib import Path
def digest(data):return hashlib.sha256(data).hexdigest()
def main():
    p=argparse.ArgumentParser();p.add_argument('--install',type=Path,required=True);p.add_argument('--base-source',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    install=json.loads(a.install.read_text());source=Path(install['source']);manifest=install.get('experimental',{})
    a.output.mkdir(parents=True,exist_ok=False);files=[];patch=[]
    inputs=a.install.parent/'build-inputs.json';assert digest(inputs.read_bytes())==install['build_inputs_sha256']
    pinned={item['path']:item['sha256'] for item in json.loads(inputs.read_text())['inputs']}
    names={'matron/src/emu_bridge.c'} | {item['path'] for item in manifest.get('files',[])}
    for name in sorted(names):
        old=(a.base_source/name).read_bytes();data=(source/name).read_bytes();assert digest(data)==pinned[name]
        if name=='matron/src/emu_bridge.c':
            marker=b'    if (size>32760)'
            assert data.count(marker)==1
            seam=b'    /* Test-only forced scheduling window after the connected check. */\n    if(port==0 && size==3 && data[0]==176 && data[1]==90) { fprintf(stderr,"EMU_SEND_RACE_ENTER\\n");fflush(stderr);usleep(250000); }\n'
            data=data.replace(marker,seam+marker)
        files.append(dict(path=name,before_sha256=digest(old),after_sha256=digest(data)))
        patch.extend(difflib.unified_diff(old.decode().splitlines(True),data.decode().splitlines(True),fromfile='a/'+name,tofile='b/'+name))
    content=''.join(patch).encode();(a.output/'controlled-runtime.patch').write_bytes(content)
    manifest=dict(manifest,files=files,patch_sha256=digest(content),test_only_send_race_delay_us=250000,derived_from_install=str(a.install),derived_install_sha256=digest(a.install.read_bytes()))
    (a.output/'candidate.json').write_text(json.dumps(manifest,indent=2)+'\n');print(a.output)
if __name__=='__main__':main()
