"""Run existing generic device conformance on an explicit real-time adapter."""
import argparse,json,sys
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'src'),str(ROOT/'tests')]
from automation import session
from automation.identity import artifact,source_identity
from automation.protocol import ContractError,read_json,write_json
from runtime.dependencies import verify_install
import grid_native,midi_native


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--install',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True);args=parser.parse_args();args.output.mkdir(parents=True,exist_ok=False)
    install=read_json(args.install);verify_install(install);source=source_identity()
    expected={'matron/src/emu_bridge.c','matron/wscript','matron/src/emu_midi_schedule.c','matron/src/emu_midi_schedule.h'}
    assert install['experimental']['status']=='device-adapter-unadmitted'
    assert {f['path'] for f in install['experimental']['files']}==expected,'Adapter changes more than the device boundary'
    original=session.start;results=[];failure=None
    def selected(*args_,**kwargs):
        kwargs['experimental_install']=str(args.install.resolve())
        return original(*args_,**kwargs)
    try:
        # This changes only the public installation argument and artifact roots;
        # all original native device interactions and assertions run unchanged.
        with patch.object(session,'start',selected),patch.object(grid_native.Client,'output_root',args.output/'grid',create=True),patch.object(midi_native.Client,'output_root',args.output/'midi',create=True):
            results.append(grid_native.conformance())
            results.append(midi_native.roundtrip())
            results.append(midi_native.overflow())
        try:
            opened=original('native',script=ROOT/'fixtures/probes/midi-probe/midi-probe.lua',code_root=ROOT/'fixtures/probes',
                clock_mode='controlled-experimental',experimental_install=str(args.install.resolve()))
        except ContractError as error:
            assert error.code=='clock_mode',error
            results.append(dict(name='device-adapter-rejects-controlled-clock',passed=True))
        else:
            session.stop(opened['session_id'])
            raise AssertionError('Device adapter exposed experimental controlled time')
        assert source_identity()['digest']==source['digest'],'Sources changed during conformance'
        assert len(results)==4 and all(r['passed'] for r in results)
    except Exception as error:failure=repr(error)
    record=dict(passed=failure is None,source=source,results=results,error=failure,
        artifacts=[artifact(p,args.output) for p in sorted(args.output.rglob('*')) if p.is_file()])
    write_json(args.output/'manifest.json',record);print(args.output/'manifest.json')
    return int(failure is not None)


if __name__=='__main__':raise SystemExit(main())
