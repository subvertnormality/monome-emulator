"""Pin a tested device-only candidate after proving its compiled inputs match the lock.

Use after native adapter conformance. This changes the local default installation,
not release/admission status. It preserves the previous descriptor and lock, and
does not rewrite any running session's binaries or shared libraries.
"""
import argparse,copy,hashlib,json,sys,tempfile,uuid
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from automation.protocol import read_json,write_json
from runtime.dependencies import verify_install
from locked_native_source import reconstruct,content_manifest


def sha(data):return hashlib.sha256(data).hexdigest()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--install',type=Path,required=True);parser.add_argument('--recipe',type=Path,required=True)
    args=parser.parse_args();candidate=read_json(args.install);verify_install(candidate)
    manifest=read_json(args.recipe/'candidate.json')
    assert candidate['experimental']==manifest and manifest['status']=='device-adapter-unadmitted'
    assert manifest['midi_schedule_domains']==['monotonic']
    patch=(args.recipe/'controlled-runtime.patch').read_bytes();assert sha(patch)==manifest['patch_sha256']
    original=(ROOT/'dependencies.lock.json').read_bytes();previous=(ROOT/'.runtime/current.json').read_bytes()
    verify_install(json.loads(previous));lock=json.loads(original)
    name='patches/norns/0012-scheduled-midi-input.patch'
    assert all(p['path']!=name for p in lock['patches']),'Device queue already pinned'
    path=ROOT/name
    if path.exists():assert path.read_bytes()==patch,'Preserve a different existing patch'
    else:path.write_bytes(patch)
    lock['patches'].append(dict(path=name,sha256=sha(patch)))
    compiled=(args.install.parent/'build-inputs.json').read_bytes()
    assert sha(compiled)==candidate['build_inputs_sha256'],'Candidate build provenance changed'
    with tempfile.TemporaryDirectory(prefix='norns-device-pin-') as temp:
        source=Path(temp)/'source';provenance=reconstruct(ROOT,lock,source)
        provenance['inputs']=content_manifest(source)
        assert provenance['inputs']==json.loads(compiled)['inputs'],'New lock differs from compiled source bytes/modes'
    new_lock=(json.dumps(lock,indent=2)+'\n').encode();digest=sha(new_lock)
    directory=ROOT/'.runtime/builds'/digest[:16];directory.mkdir(parents=True,exist_ok=False)
    archive=ROOT/'.runtime/admissions'/('device-queue-'+uuid.uuid4().hex);archive.mkdir(parents=True)
    (archive/'previous-lock.json').write_bytes(original);(archive/'previous-installation.json').write_bytes(previous)
    (archive/'candidate-build-inputs.json').write_bytes(compiled)
    write_json(directory/'build-inputs.json',provenance)
    install=copy.deepcopy(candidate);del install['experimental']
    install.update(lock_sha256=digest,patches=lock['patches'],build_inputs_sha256=sha((directory/'build-inputs.json').read_bytes()))
    assert (ROOT/'dependencies.lock.json').read_bytes()==original and (ROOT/'.runtime/current.json').read_bytes()==previous,'Default changed during pinning'
    try:
        (ROOT/'dependencies.lock.json').write_bytes(new_lock)
        verify_install(install)
        write_json(directory/'installation.json',install);write_json(ROOT/'.runtime/current.json',install)
        write_json(archive/'promotion.json',dict(previous_lock_sha256=sha(original),lock_sha256=digest,
            candidate_installation_sha256=sha(args.install.read_bytes()),installation=str(directory/'installation.json'),
            compiled_inputs_equal=True,binaries_rebuilt=False,controlled_time_enabled=False,release_admitted=False))
    except Exception:
        (ROOT/'dependencies.lock.json').write_bytes(original);(ROOT/'.runtime/current.json').write_bytes(previous)
        raise
    print(directory/'installation.json');print(archive/'promotion.json')


if __name__=='__main__':main()
