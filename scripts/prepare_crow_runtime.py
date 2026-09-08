"""Attach a new identified Crow helper to an existing Crow-enabled native build."""
import argparse,hashlib,json,shutil,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from runtime.dependencies import verify_install
from crow_source import verify_lua_files

def main():
    p=argparse.ArgumentParser();p.add_argument('--install',type=Path,required=True)
    p.add_argument('--crow-build',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    install=json.loads(a.install.read_text());verify_install(install)
    if not install.get('experimental',{}).get('crow'):raise ValueError('Base must contain the native Crow device hook')
    build=a.crow_build.resolve();manifest=json.loads((build/'manifest.json').read_text())
    lua_identity=verify_lua_files(manifest)
    out=a.output.resolve();out.mkdir(parents=True,exist_ok=False)
    serial=Path(manifest.get('serial_path',ROOT/'src/devices/crow_host/serial.lua'))
    if hashlib.sha256(serial.read_bytes()).hexdigest()!=manifest['adapter']['serial.lua']:raise ValueError('Crow serial adapter changed')
    shutil.copyfile(serial,out/'serial.lua');manifest['serial_path']=str(out/'serial.lua')
    source=Path(manifest['source']);binary=build/'crow-host'
    install['binaries']['crow_host']=dict(path=str(binary),sha256=manifest['binary_sha256'])
    install['experimental']['crow']=dict(source=str(source),manifest=manifest,
        lua_files=lua_identity)
    install['experimental']['crow_parent_install_sha256']=hashlib.sha256(a.install.read_bytes()).hexdigest()
    verify_install(install)
    (out/'installation.json').write_text(json.dumps(install,indent=2)+'\n');print(out/'installation.json')
if __name__=='__main__':main()
