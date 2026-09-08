"""Reconstruct an opt-in audio runtime; never promote or edit the current build."""
import argparse, difflib, hashlib, json, os, shutil, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from runtime.dependencies import command, runtime_content, verify_install
from locked_native_source import reconstruct, content_manifest

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--crow-build', type=Path, help='Opt-in identified Crow host build')
    args = parser.parse_args()
    out = args.output.resolve(); out.mkdir(parents=True, exist_ok=False)
    base = json.loads((ROOT / '.runtime/current.json').read_text()); verify_install(base)
    source = out / 'norns'; lock = json.loads((ROOT / 'dependencies.lock.json').read_text())
    provenance = reconstruct(ROOT, lock, source)
    path = source / 'matron/src/weaver.c'
    before = path.read_text()
    guard = '    if (emu_enabled() && strcmp(s,"None")!=0) return luaL_error(l,"unsupported emulator audio engine: %s",s);\n'
    if before.count(guard) != 1: raise ValueError('Expected engine guard changed')
    after = before.replace(guard, '')
    path.write_text(after)
    patch = ''.join(difflib.unified_diff(before.splitlines(True), after.splitlines(True),
                 fromfile='a/matron/src/weaver.c', tofile='b/matron/src/weaver.c'))
    crow_manifest=None
    if args.crow_build:
        crow_build=args.crow_build.resolve();crow_manifest=json.loads((crow_build/'manifest.json').read_text())
        from crow_source import verify_lua_files
        crow_lua_identity=verify_lua_files(crow_manifest)
        binary=crow_build/'crow-host'
        if hashlib.sha256(binary.read_bytes()).hexdigest()!=crow_manifest['binary_sha256']:raise ValueError('Crow host changed')
        bridge=source/'matron/src/emu_bridge.c';before=bridge.read_text()
        marker='    grid_metadata();\n}'
        if before.count(marker)!=1:raise ValueError('Crow device hook insertion changed')
        after=before.replace(marker,'    grid_metadata();\n    const char *crow_path=getenv("NORNS_EMU_CROW_PATH");\n    if(crow_path) dev_list_add(DEV_TYPE_CROW,crow_path,"Virtual Crow",NULL);\n}')
        bridge.write_text(after)
        patch+=''.join(difflib.unified_diff(before.splitlines(True),after.splitlines(True),fromfile='a/matron/src/emu_bridge.c',tofile='b/matron/src/emu_bridge.c'))
        from crow_native_patch import apply as patch_crow_events
        patch+=patch_crow_events(source)
    from prepare_audio_mod_runtime import apply_default_server
    default_server_patch=apply_default_server(source)
    patch+=default_server_patch
    from prepare_engine_ready import apply_engine_ready
    engine_ready_patch=apply_engine_ready(source)
    patch+=engine_ready_patch
    (out / 'engine-ready.patch').write_text(engine_ready_patch)
    (out / 'default-server.patch').write_text(default_server_patch)
    (out / 'audio-runtime.patch').write_text(patch)
    # The existing launcher includes sc/core recursively. Keep official engine
    # bytes unchanged and within its existing interpreted-content hash boundary.
    shutil.copytree(source / 'sc/engines', source / 'sc/core/engines')
    provenance['inputs'] = content_manifest(source)
    (out / 'build-inputs.json').write_text(json.dumps(provenance, indent=2) + '\n')
    prefix = Path(base['prefix']); log = out / 'build.log'
    env = dict(os.environ, GIT_CEILING_DIRECTORIES=str(source.parent),
               CFLAGS='-I' + str(prefix / 'include') + ' -Wno-error=unused-result',
               LDFLAGS='-L' + str(prefix / 'lib'))
    command(['python3', 'waf', 'configure', '--desktop'], source, log, env)
    command(['python3', 'waf', 'build', '--targets=matron,crone', '-j8'], source, log, env)
    binaries = {}
    for name, p in [('matron', source/'build/matron/matron'), ('crone', source/'build/crone/crone'),
                    ('libmonome', prefix/'lib/libmonome.so')]:
        binaries[name] = dict(path=str(p), sha256=hashlib.sha256(p.read_bytes()).hexdigest())
    if crow_manifest:binaries['crow_host']=dict(path=str(crow_build/'crow-host'),sha256=crow_manifest['binary_sha256'])
    install = dict(base, source=str(source), binaries=binaries, interpreted_files=runtime_content(source),
        experimental=dict(status='audio-feasibility-only', patch_sha256=hashlib.sha256(patch.encode()).hexdigest(),
                          default_server_patch_sha256=hashlib.sha256(default_server_patch.encode()).hexdigest(),
                          engine_ready_patch_sha256=hashlib.sha256(engine_ready_patch.encode()).hexdigest(),
                          engine_sources='Pinned official sc/engines copied unchanged into sc/core/engines'),
        build_inputs_sha256=hashlib.sha256((out/'build-inputs.json').read_bytes()).hexdigest())
    if crow_manifest:
        crow_source=Path(crow_manifest['source'])
        install['experimental']['crow']=dict(source=str(crow_source),manifest=crow_manifest,
            lua_files=crow_lua_identity)
    (out/'installation.json').write_text(json.dumps(install, indent=2)+'\n')
    verify_install(install); print(out/'installation.json', flush=True)

if __name__ == '__main__': main()
