"""Composition rejects changed/added Lua without touching shared official source."""
import argparse,json,shutil,subprocess,sys,tempfile,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from crow_source import lua_files,verify_lua_files

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--build',type=Path);parser.add_argument('--install',type=Path);args=parser.parse_args()
    with tempfile.TemporaryDirectory() as directory:
        source=Path(directory);(source/'lua').mkdir();path=source/'lua/output.lua';path.write_text('return 1\n')
        manifest=dict(source=str(source),lua_files=lua_files(source))
        assert verify_lua_files(manifest)==manifest['lua_files']
        for change in ('modified','added','missing-identity'):
            path.write_text('return 2\n' if change=='modified' else 'return 1\n')
            if change=='added':(source/'lua/extra.lua').write_text('return 0\n')
            else:(source/'lua/extra.lua').unlink(missing_ok=True)
            value=dict(manifest)
            if change=='missing-identity':value.pop('lua_files')
            try:verify_lua_files(value)
            except ValueError:pass
            else:raise AssertionError('Accepted '+change)
    print('PASS Crow Lua identity: original, modified, added and missing identity')
    if args.build:
        assert args.install,'--install required for composition negative checks'
        out=ROOT/'artifacts/crow'/time.strftime('composition-identity-%Y%m%d-%H%M%S');out.mkdir(parents=True)
        manifest=json.loads((args.build/'manifest.json').read_text())
        source=out/'source';shutil.copytree(Path(manifest['source'])/'lua',source/'lua')
        manifest['source']=str(source)
        build=out/'build';build.mkdir();(build/'crow-host').symlink_to((args.build/'crow-host').resolve())
        (build/'manifest.json').write_text(json.dumps(manifest))
        (source/'lua/output.lua').write_text('error("deliberate changed Lua")\n')
        checks=[]
        for script,extra in [('prepare_crow_runtime.py',['--install',str(args.install)]),('build_audio_candidate.py',[])]:
            result=subprocess.run([sys.executable,str(ROOT/'scripts'/script),'--crow-build',str(build),
                                   '--output',str(out/script),*extra],capture_output=True,text=True,timeout=120)
            (out/(script+'.stderr')).write_text(result.stderr)
            assert result.returncode!=0 and 'Crow Lua changed since validated host build' in result.stderr,result.stderr
            checks.append(script)
        (out/'report.json').write_text(json.dumps(dict(passed=True,checks=checks),indent=2)+'\n');print(out)
if __name__=='__main__':main()
