"""CLI routes are generic; application fixtures never control core dispatch."""
import argparse
import json
from pathlib import Path
import platform
import shutil
import sys
import subprocess
from . import evidence,runner,session
from .protocol import ContractError,ROOT,read_json,uid

def main(argv=None):
    parser=argparse.ArgumentParser(prog='emu')
    commands=parser.add_subparsers(dest='command',required=True)
    doctor=commands.add_parser('doctor'); doctor.add_argument('--json',action='store_true')
    start=commands.add_parser('start'); start.add_argument('--backend',default='native',choices=['native','contract-fixture'])
    start.add_argument('--script'); start.add_argument('--code-root'); start.add_argument('--data'); start.add_argument('--profile',default='wsl')
    start.add_argument('--fixture'); start.add_argument('--fixture-profile',default='base-midi')
    start.add_argument('--midi-config',help='JSON with ordered virtual port names and optional capture_limit')
    start.add_argument('--random-seed',type=int,help='Opt-in repeatable native Lua seed, including script reseeding')
    start.add_argument('--experimental-install',help='Use an identified experimental installation without promoting it')
    start.add_argument('--no-crow',action='store_true',help='Leave the optional virtual Crow disconnected for this session')
    start.add_argument('--audio-file',action='append',default=[],help='Copy a host sample into this session audio directory; repeat for multiple files')
    start.add_argument('--audio-directory',help='Copy an audio directory tree into this isolated session, preserving relative paths')
    start.add_argument('--input-timeout',type=float,default=2,help='Native input completion deadline in seconds (0.1–30, default 2)')
    start.add_argument('--arc',action='store_true',help='Enable virtual arc on an identified experimental arc runtime')
    fetch=commands.add_parser('fetch'); fetch.add_argument('--locked',action='store_true',required=True)
    commands.add_parser('build')
    fixtures=commands.add_parser('fixtures'); fixture_commands=fixtures.add_subparsers(dest='fixture_command',required=True)
    fixture_fetch=fixture_commands.add_parser('fetch'); fixture_fetch.add_argument('name'); fixture_fetch.add_argument('--locked',action='store_true',required=True)
    for name in ['snapshot','stop','capabilities']:
        command=commands.add_parser(name); command.add_argument('session_id')
    action=commands.add_parser('action'); action.add_argument('session_id'); action.add_argument('json_action')
    run=commands.add_parser('run'); run.add_argument('scenario')
    verify=commands.add_parser('verify-evidence'); verify.add_argument('manifest')
    replay=commands.add_parser('replay'); replay.add_argument('manifest')
    release=commands.add_parser('release-check'); release.add_argument('--milestone',required=True); release.add_argument('--profile',required=True); release.add_argument('manifests',nargs='*')
    tests=commands.add_parser('test'); tests.add_argument('--suite',required=True); tests.add_argument('--require-all',action='store_true')
    args=parser.parse_args(argv)
    try:
        if args.command=='doctor':
            result=dict(platform=platform.platform(),kernel=platform.release(),python=sys.version,
                tools={k:shutil.which(k) for k in ['gcc','lua5.3','jackd','sclang']},
                capability='native MIDI-only norns profile; run capabilities on a session for supported boundaries',
                native_installation=(ROOT/'.runtime/current.json').exists(),
                native_probe_available=(ROOT/'artifacts/c00/native-probe.json').exists())
        elif args.command=='fetch':
            from runtime.dependencies import fetch
            result=fetch()
        elif args.command=='build':
            from runtime.dependencies import build
            result=build()
        elif args.command=='fixtures':
            import app_fixtures
            result=app_fixtures.fetch(args.name)
        elif args.command=='start':
            midi_config=read_json(args.midi_config) if args.midi_config else None
            if args.fixture:
                if args.script or args.code_root: raise ContractError('fixture_inputs','Choose either a fixture or external script inputs')
                import app_fixtures
                options=app_fixtures.launch_options(args.fixture,args.fixture_profile)
                result=session.start(args.backend,data=args.data,midi_config=midi_config,random_seed=args.random_seed,experimental_install=args.experimental_install,crow_enabled=not args.no_crow,audio_files=args.audio_file,audio_directory=args.audio_directory,input_timeout=args.input_timeout,arc_enabled=args.arc,**options)
            else: result=session.start(args.backend,args.script,args.code_root,args.data,midi_config=midi_config,random_seed=args.random_seed,experimental_install=args.experimental_install,crow_enabled=not args.no_crow,audio_files=args.audio_file,audio_directory=args.audio_directory,input_timeout=args.input_timeout,arc_enabled=args.arc)
        elif args.command=='snapshot': result=session.request(args.session_id,'/snapshot')
        elif args.command=='capabilities': result=session.request(args.session_id,'/capabilities')
        elif args.command=='stop': result=session.stop(args.session_id)
        elif args.command=='action':
            info=session.request(args.session_id,'/health')
            result=session.request(args.session_id,'/action',dict(schema_version=1,session_id=args.session_id,action_id=uid(),
                sequence=info['sequence']+1,action=json.loads(args.json_action)))
        elif args.command=='verify-evidence':
            value=evidence.verify(args.manifest); result=dict(passed=True,run_id=value['run_id'],fidelity=value['fidelity'])
        elif args.command in ('run','replay'):
            replay_of=None
            if args.command=='replay':
                original=evidence.replay_input(args.manifest)
                replay_of=dict(manifest=str(Path(args.manifest).resolve()),run_id=original['run_id'],source_digest=original['source']['digest'],prior_passed=original['passed'],execution='current-source')
            if replay_of and original.get('kind')=='native-package':
                command=read_json(ROOT/'compatibility/packages.json')['packages'][original['scenario_id']]['command']
                print(json.dumps(dict(replay_of=replay_of,package=original['scenario_id'])),flush=True)
                return subprocess.call([sys.executable,*command],cwd=ROOT)
            path=args.scenario if args.command=='run' else str(Path(args.manifest).resolve().parent/original['scenario']['path'])
            manifest,value=runner.run(path,replay_of=replay_of); print(json.dumps(dict(manifest=str(manifest),passed=value['passed'],error=value['error'])))
            return value['exit_code']
        elif args.command=='release-check': result=evidence.release_check(args.manifests,args.milestone,args.profile)
        elif args.command=='test':
            if args.suite!='contracts': raise ContractError('unknown_suite','Suite not implemented: '+args.suite)
            import unittest
            suite=unittest.defaultTestLoader.discover(str(ROOT/'tests/contracts'))
            count=suite.countTestCases()
            if count==0: raise ContractError('empty_selection','No tests collected')
            result=unittest.TextTestRunner(verbosity=2).run(suite)
            print(json.dumps(dict(suite='contracts',collected=count,passed=result.wasSuccessful(),skipped=len(result.skipped))))
            return 0 if result.wasSuccessful() and not result.skipped else 1
        print(json.dumps(result,indent=2)); return 0
    except (ContractError,ValueError,OSError) as error:
        value=error.as_dict() if isinstance(error,ContractError) else ContractError('command_failed',str(error)).as_dict()
        print(json.dumps(value),file=sys.stderr); return 1
