"""Snapshot the measured source graph into separate runtime/application locks."""
import hashlib
import json
from pathlib import Path
import subprocess
ROOT = Path(__file__).resolve().parents[2]
def git(path, *args):
    return subprocess.check_output(['git',*args],cwd=path,text=True).strip()
def identity(path, url):
    modules = []
    for line in git(path,'submodule','status','--recursive').splitlines():
        sha,relative,*_ = line.strip().split()
        if sha.startswith(('-', '+', 'U')): raise RuntimeError('Unresolved submodule '+line)
        module = path/relative
        modules.append(dict(path=relative,commit=sha,url=git(module,'remote','get-url','origin')))
    files = [p for p in path.iterdir() if p.is_file() and ('LICENSE' in p.name.upper() or 'COPYING' in p.name.upper())]
    if path.name=='libmonome': files.append(path/'src/libmonome.c')
    return dict(url=url,commit=git(path,'rev-parse','HEAD'),submodules=modules,
      license_files=[dict(path=str(p.relative_to(path)),sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in files],
      license_status='root file recorded; transitive notices retained in source' if files else 'No root license found; do not redistribute fixture sources')
def write(name,value):
    file=ROOT/name; file.parent.mkdir(parents=True,exist_ok=True)
    file.write_text(json.dumps(value,indent=2)+'\n')
runtime = dict(schema_version=1, status='C00 feasibility; not release certification', dependencies={
 'norns':identity(ROOT/'.runtime/deps/norns','https://github.com/monome/norns.git'),
 'libmonome':identity(ROOT/'.runtime/deps/libmonome','https://github.com/monome/libmonome.git')},
 build=dict(profile='ubuntu-20.04-wsl2-x86_64',norns_configure=['--desktop'],targets=['matron','crone'],
            cflags=['-I<runtime-prefix>/include','-Wno-error=unused-result'],ldflags=['-L<runtime-prefix>/lib'],
            libmonome_configure=['--enable-embedded-protos','--prefix=<runtime-prefix>'],
            services=['JACK dummy 48000Hz/128 frames, non-realtime priority','official crone','sclang with official sc/core'],
            packages=json.loads((ROOT/'artifacts/c00/host.json').read_text())['packages']),
 patches=[dict(path=str(p.relative_to(ROOT)),sha256=hashlib.sha256(p.read_bytes()).hexdigest())
          for p in sorted((ROOT/'patches/norns').glob('*.patch'))],
 serialosc=dict(role='protocol reference; physical USB daemon not used by native virtual-device backend',
                source='https://monome.org/docs/serialosc/osc/'),
 update_candidate=dict(ref='a84ba1fcc9b0b1780be686c70876ba932508c9cc',tag='v2.9.3',
      status='Adjacent official C matron release fetched and diff inspected. C14 must build an isolated candidate and prove compatibility/rejection/rollback. No second build validated yet.',
      future_main='cc4ba9e75ff6e97165895421780a6a9e0a8e284b'))
runtime['build']['packages']['supercollider'] = subprocess.check_output(
    ['dpkg-query','-W','supercollider-language','supercollider-server'],text=True).strip()
write('dependencies.lock.json',runtime)
apps = dict(schema_version=1,fixture='mosaic',install_by_default=False,
 sources={name:identity(ROOT/'upstream'/name,url) for name,url in [
 ('mosaic','https://github.com/subvertnormality/mosaic.git'),('matrix','https://github.com/sixolet/matrix.git'),
 ('toolkit','https://github.com/sixolet/toolkit.git')]},
 profiles={'base-midi':dict(code=['mosaic'],enabled_mods=[],audio_required=False),
           'midi-modulation':dict(code=['mosaic','matrix','toolkit'],enabled_mods=['matrix','toolkit'],audio_required=False)},
 setup=['Preserve mosaic code-directory name and pinned nb submodule',
        'Copy configs into isolated data/mosaic/config before init',
        'Enable mods through native system.mods lifecycle, never by replacing params',
        'Provide Norns2sinfonion virtual MIDI output for software sync scenarios'],
 baseline='artifacts/c00/mosaic-unit.json')
write('fixtures/apps/mosaic.lock.json',apps)
print('Recorded separate runtime and application fixture source graphs')
