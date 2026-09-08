"""Build unchanged Crow ii sources/generators with a scoped host I2C boundary."""
import argparse,hashlib,json,shutil,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def main():
    p=argparse.ArgumentParser();p.add_argument('--generator-build',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    generator=a.generator_build.resolve();base=json.loads((generator/'manifest.json').read_text());source=Path(base['source'])
    assert hashlib.sha256((generator/'crow-host').read_bytes()).hexdigest()==base['binary_sha256']
    for folder,pin in base['pins'].items():
        assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=source/folder,text=True).strip()==pin
        assert not subprocess.check_output(['git','diff','HEAD','--'],cwd=source/folder)
    out=a.output.resolve();out.mkdir(parents=True,exist_ok=False)
    for folder in ('lib','build','ll'):(out/folder).mkdir()
    (out/'submodules').symlink_to(source/'submodules',target_is_directory=True)
    copied={}
    for name in ('ii.c','ii.h','l_ii_mod.c','l_ii_mod.h'):
        shutil.copyfile(source/'lib'/name,out/'lib'/name);copied[name]=hashlib.sha256((out/'lib'/name).read_bytes()).hexdigest()
    adapter=ROOT/'src/devices/crow_ii_host'
    for name in ('i2c.h','i2c_pullups.h'):shutil.copyfile(adapter/name,out/'ll'/name)
    for name in ('ii_mod_gen','ii_c_layer'):
        wrapper=out/(name+'.lua')
        wrapper.write_text('arg={'+json.dumps(str(source/'lua/ii'))+','+json.dumps(str(out/'build'/(name+'.h')))+'}\ndofile(CROW_SOURCE.."/util/'+name+'.lua")\n')
        with (out/(name+'.log')).open('w') as log:
            subprocess.run([str(generator/'crow-host'),str(source),str(wrapper)],cwd=source,stdout=log,stderr=subprocess.STDOUT,check=True)
    files=[adapter/'main.c',out/'lib/ii.c',out/'lib/l_ii_mod.c',source/'submodules/wrLib/wrQueue.c',source/'submodules/wrLib/wrMath.c']
    files+=sorted(f for f in (source/'submodules/lua/src').glob('*.c') if f.name not in ('lua.c','luac.c'))
    command=['gcc','-std=gnu11','-O2','-DLUA_USE_LINUX','-Wl,--wrap=printf','-Wl,--wrap=puts']
    command+=['-I'+str(d) for d in (adapter,ROOT/'src/devices/crow_host',out/'lib',source/'lib',source/'submodules/wrLib')]
    command+=list(map(str,files))+['-lm','-ldl','-o',str(out/'crow-ii-host')]
    with (out/'build.log').open('w') as log:subprocess.run(command,stdout=log,stderr=subprocess.STDOUT,check=True)
    manifest=dict(source=str(source),pins=base['pins'],generator_sha256=base['binary_sha256'],command=command,copied_sources=copied,
        generated={f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in (out/'build').iterdir()},
        descriptors={f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in (source/'lua/ii').glob('*.lua')},
        adapter={f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in adapter.iterdir() if f.is_file()},
        binary_sha256=hashlib.sha256((out/'crow-ii-host').read_bytes()).hexdigest())
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');print(out/'crow-ii-host')
if __name__=='__main__':main()
