"""Reconstruct native inputs from Git objects, never a mutable build checkout."""
import hashlib
import os
from pathlib import Path
import subprocess
import tempfile


def git(repo,*args):
    return subprocess.check_output(['git','-C',str(repo),*args],text=True).strip()


def export_revision(repo,revision,destination):
    """Archive committed bytes/modes; tracked edits and extra files cannot enter."""
    destination=Path(destination);destination.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='norns-source-') as temporary:
        archive=Path(temporary)/'source.tar'
        subprocess.run(['git','-C',str(repo),'archive','--format=tar',f'--output={archive}',revision],check=True)
        subprocess.run(['tar','-xf',str(archive),'-C',str(destination)],check=True)


def reconstruct(root,lock,destination):
    root=Path(root);destination=Path(destination)
    entry=lock['dependencies']['norns'];cache=root/'.runtime/deps/norns'
    if entry['url']!='https://github.com/monome/norns.git':raise ValueError('Official norns origin required')
    if git(cache,'remote','get-url','origin')!=entry['url']:raise ValueError('Unexpected cached norns origin')
    # Verify every nested gitlink against the lock, rather than trusting the
    # checked-out submodule HEAD or excluding an unlisted dependency silently.
    expected={m['path']:m['commit'] for m in entry['submodules']};observed={}
    def visit(repo,revision,prefix=''):
        for line in git(repo,'ls-tree','-r',revision).splitlines():
            mode,kind,rest=line.split(' ',2);sha,path=rest.split('\t',1)
            if mode!='160000':continue
            full=prefix+path;observed[full]=sha
            if expected.get(full)!=sha:raise ValueError('Unpinned submodule: '+full)
            visit(cache/full,sha,full+'/')
    visit(cache,entry['commit'])
    if observed!=expected:raise ValueError('Locked submodule graph differs from Git objects')
    destination.mkdir(parents=True,exist_ok=False)
    export_revision(cache,entry['commit'],destination)
    for path,revision in sorted(expected.items()):export_revision(cache/path,revision,destination/path)
    env=dict(os.environ,GIT_CEILING_DIRECTORIES=str(destination.parent))
    for item in lock['patches']:
        path=root/item['path']
        if hashlib.sha256(path.read_bytes()).hexdigest()!=item['sha256']:raise ValueError('Changed declared patch: '+item['path'])
        subprocess.run(['git','apply','--check',str(path)],cwd=destination,env=env,check=True)
        subprocess.run(['git','apply',str(path)],cwd=destination,env=env,check=True)
    return dict(norns_revision=entry['commit'],submodules=expected,patches=lock['patches'])


def content_manifest(source):
    """Retain all reconstructed build inputs before configure generates files."""
    return [dict(path=p.relative_to(source).as_posix(),sha256=hashlib.sha256(p.read_bytes()).hexdigest(),
                 executable=bool(p.stat().st_mode & 0o111))
            for p in sorted(source.rglob('*')) if p.is_file()]
