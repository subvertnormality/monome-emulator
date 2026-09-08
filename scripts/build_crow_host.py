"""Compile official Crow CASL/slopes and pinned Lua for an isolated host probe."""
import argparse, hashlib, json, shutil, subprocess
from pathlib import Path
from crow_source import pinned_lua_files
ROOT=Path(__file__).resolve().parents[1]
def main():
    p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--ii-build',type=Path);a=p.parse_args()
    source=a.source.resolve();out=a.output.resolve();out.mkdir(parents=True,exist_ok=False)
    pins={'.':'b340579d94e57e2b43336611b2c4037cff74bb80','submodules/lua':'32ffee2104c3a19ad2122dbfc5d4a018c273afc7','submodules/wrDsp':'e1eb9c533fbdec9d68438b22b5cdf179247fd02b','submodules/wrLib':'c44e6b0ff9846ddf69e6f15f3357e2df638fb0f6'}
    for folder,pin in pins.items():
        if subprocess.check_output(['git','rev-parse','HEAD'],cwd=source/folder,text=True).strip()!=pin:raise ValueError('Wrong Crow source revision')
        if subprocess.check_output(['git','diff','HEAD','--'],cwd=source/folder):raise ValueError('Modified Crow source')
    adapter=ROOT/'src/devices/crow_host'
    lua_identity=pinned_lua_files(source)
    portable=out/'core';portable.mkdir()
    for name in ('detect.c','detect.h'):shutil.copyfile(source/'lib'/name,portable/name)
    files=[adapter/'main.c']+[source/'lib'/name for name in ['casl.c','slopes.c','shapes.c']]+[source/'submodules/wrDsp/wrBlocks.c']
    files+=[portable/'detect.c',source/'submodules/wrLib/wrMeters.c',source/'submodules/wrDsp/wrFilter.c',source/'submodules/wrLib/wrMath.c']
    files+=sorted(f for f in (source/'submodules/lua/src').glob('*.c') if f.name not in ('lua.c','luac.c'))
    ii_flags=[];ii_manifest=None
    if a.ii_build:
        ii_build=a.ii_build.resolve();ii_manifest=json.loads((ii_build/'manifest.json').read_text())
        if ii_manifest['pins']!=pins:raise ValueError('ii source pins differ')
        for folder,key in [('lib','copied_sources'),('build','generated')]:
            (out/folder).mkdir()
            for name,digest in ii_manifest[key].items():
                original=ii_build/folder/name
                if hashlib.sha256(original.read_bytes()).hexdigest()!=digest:raise ValueError('Changed ii build source')
                shutil.copyfile(original,out/folder/name)
        (out/'submodules').symlink_to(source/'submodules',target_is_directory=True)
        (out/'ll').mkdir()
        ii_adapter=ROOT/'src/devices/crow_ii_host'
        for name in ('i2c.h','i2c_pullups.h'):shutil.copyfile(ii_adapter/name,out/'ll'/name)
        files += [out/'lib/ii.c',out/'lib/l_ii_mod.c',source/'submodules/wrLib/wrQueue.c']
        ii_flags=['-DCROW_HOST_II','-Wl,--wrap=printf','-Wl,--wrap=puts','-I'+str(out/'lib'),'-I'+str(ii_adapter)]
    command=['gcc','-std=gnu11','-O2','-DLUA_USE_LINUX','-I'+str(adapter),'-I'+str(portable),'-I'+str(source/'submodules/wrLib'),'-I'+str(source/'submodules/wrDsp'),'-I'+str(source/'lib'),'-I'+str(source)]+list(map(str,files))+['-lm','-ldl','-o',str(out/'crow-host')]
    command[1:1]=ii_flags
    with (out/'build.log').open('w') as log:subprocess.run(command,stdout=log,stderr=subprocess.STDOUT,check=True)
    shutil.copyfile(adapter/'serial.lua',out/'serial.lua')
    manifest=dict(lua_files=lua_identity,input_protocol=1,serial_path=str(out/'serial.lua'),capture_protocol=1,pins=pins,source=str(source),command=command,portable_sources={f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in portable.iterdir()},binary_sha256=hashlib.sha256((out/'crow-host').read_bytes()).hexdigest(),
                  adapter={str(f.relative_to(adapter)):hashlib.sha256(f.read_bytes()).hexdigest() for f in adapter.iterdir() if f.is_file()})
    if ii_manifest:
        manifest.update(ii_protocol=1,ii_build=ii_manifest,ii_adapter={f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in ii_adapter.iterdir() if f.is_file()})
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');print(out/'crow-host')
if __name__=='__main__':main()
