"""Prepare the native device queue alone, without experimental clock changes."""
import argparse,difflib,hashlib,json
from pathlib import Path
from prepare_midi_schedule import transform
ROOT=Path(__file__).resolve().parents[1]


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source',type=Path,required=True);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();args.output.mkdir(parents=True,exist_ok=False)
    original={};changed={}
    bridge='matron/src/emu_bridge.c';original[bridge]=(args.source/bridge).read_text()
    assert 'emu_midi_schedule.h' not in original[bridge],'Queue already installed; preserve the source'
    changed[bridge]=transform(original[bridge])
    assert 'emu_clock' not in changed[bridge],'Device-only adapter must not import the experimental clock'
    build='matron/wscript';original[build]=(args.source/build).read_text()
    old="        'src/emu_bridge.c',";assert original[build].count(old)==1
    changed[build]=original[build].replace(old,old+"\n        'src/emu_midi_schedule.c',")
    for name in ('emu_midi_schedule.c','emu_midi_schedule.h'):
        rel='matron/src/'+name;original[rel]='';changed[rel]=(ROOT/'src/runtime/native_clock'/name).read_text()
    patch=[];files=[]
    for name,after in changed.items():
        before=original[name]
        patch.extend(difflib.unified_diff(before.splitlines(True),after.splitlines(True),fromfile='a/'+name if before else '/dev/null',tofile='b/'+name))
        files.append(dict(path=name,before_sha256=hashlib.sha256(before.encode()).hexdigest(),after_sha256=hashlib.sha256(after.encode()).hexdigest()))
    # Same build-candidate input format; no default installation is selected.
    path=args.output/'controlled-runtime.patch';path.write_text(''.join(patch))
    (args.output/'candidate.json').write_text(json.dumps(dict(status='device-adapter-unadmitted',files=files,
        midi_schedule_domains=['monotonic'],patch_sha256=hashlib.sha256(path.read_bytes()).hexdigest()),indent=2)+'\n')
    print(args.output)


if __name__=='__main__':main()
