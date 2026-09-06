"""Fetch official locked sources and build an isolated native installation."""
import hashlib
from pathlib import Path
import subprocess
from automation.protocol import ROOT,ContractError,read_json,write_json

def runtime_content(source):
    """Hash all interpreted upstream code loaded after native compilation."""
    source=Path(source); files={}
    for folder in ('lua','sc/core'):
        for path in sorted((source/folder).rglob('*')):
            if path.is_file(): files[path.relative_to(source).as_posix()]=hashlib.sha256(path.read_bytes()).hexdigest()
    return files

def verify_install(install):
    if install['lock_sha256']!=hashlib.sha256((ROOT/'dependencies.lock.json').read_bytes()).hexdigest():
        raise ContractError('stale_build','Runtime lock changed; run emu build')
    for name,record in install['binaries'].items():
        if hashlib.sha256(Path(record['path']).read_bytes()).hexdigest()!=record['sha256']:
            raise ContractError('changed_binary','Runtime binary differs: '+name)
    if install.get('interpreted_files')!=runtime_content(install['source']):
        raise ContractError('changed_runtime','Installed Lua/SuperCollider source differs; rebuild a clean candidate')

def command(args,cwd,log=None,env=None):
    result=subprocess.run(args,cwd=cwd,env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
    if log:
        with open(log,'a') as stream: stream.write('$ '+' '.join(str(a) for a in args)+'\n'+result.stdout)
    if result.returncode: raise ContractError('dependency_command',str(args[0])+' failed ('+str(result.returncode)+'); '+str(log or result.stdout[-1500:]))
    return result.stdout.strip()

def fetch_source(destination,entry,log):
    destination=Path(destination); destination.parent.mkdir(parents=True,exist_ok=True)
    if not destination.exists():
        command(['git','clone','--depth','1','--no-checkout',entry['url'],str(destination)],ROOT,log)
        command(['git','fetch','--depth','1','origin',entry['commit']],destination,log)
        command(['git','checkout','--detach',entry['commit']],destination,log)
    if command(['git','remote','get-url','origin'],destination)!=entry['url']:
        raise ContractError('source_origin','Unexpected origin in '+str(destination))
    actual=command(['git','rev-parse','HEAD'],destination)
    if actual!=entry['commit']:
        raise ContractError('source_revision','Existing checkout differs; preserving it: '+str(destination))
    command(['git','submodule','update','--init','--recursive','--depth','1'],destination,log)
    expected={m['path']:m['commit'] for m in entry['submodules']}
    observed={}
    for line in command(['git','submodule','status','--recursive'],destination).splitlines():
        sha,path,*_=line.strip().split(); observed[path]=sha
    if expected!=observed: raise ContractError('submodule_identity','Resolved submodules differ from lock')
    return destination

def fetch():
    lock=read_json(ROOT/'dependencies.lock.json')
    if lock['dependencies']['norns']['url']!='https://github.com/monome/norns.git':
        raise ContractError('runtime_origin','Runtime must use official monome/norns')
    log=ROOT/'artifacts/fetch.log'; log.parent.mkdir(exist_ok=True)
    for name,entry in lock['dependencies'].items(): fetch_source(ROOT/'.runtime/deps'/name,entry,log)
    return dict(status='fetched',components=list(lock['dependencies']))

def build():
    import os
    lockfile=ROOT/'dependencies.lock.json'; lock=read_json(lockfile)
    digest=hashlib.sha256(lockfile.read_bytes()).hexdigest()
    prefix=ROOT/'.runtime/prefix'; cache=ROOT/'.runtime/deps'
    directory=ROOT/'.runtime/builds'/digest[:16]; directory.mkdir(parents=True,exist_ok=True)
    log=directory/'build.log'
    source=directory/'norns'
    if (directory/'installation.json').exists():
        install=read_json(directory/'installation.json')
        verify_install(install)
        write_json(ROOT/'.runtime/current.json',install); return install
    for name,entry in lock['dependencies'].items():
        if not (cache/name/'.git').exists(): raise ContractError('missing_dependency','Run emu fetch --locked first')
        if command(['git','rev-parse','HEAD'],cache/name)!=entry['commit']: raise ContractError('source_revision',name)
    if source.exists(): raise ContractError('incomplete_build','Previous candidate incomplete; inspect '+str(log)+' and use a new candidate directory after diagnosis')
    command(['git','clone','--shared','--no-checkout',str(cache/'norns'),str(source)],ROOT,log)
    command(['git','checkout','--detach',lock['dependencies']['norns']['commit']],source,log)
    command(['git','submodule','update','--init','--recursive','--depth','1'],source,log)
    expected={m['path']:m['commit'] for m in lock['dependencies']['norns']['submodules']}
    observed={line.strip().split()[1]:line.strip().split()[0] for line in command(['git','submodule','status','--recursive'],source).splitlines()}
    if observed!=expected: raise ContractError('submodule_identity','Build source graph differs from lock')
    for patch in lock['patches']:
        path=ROOT/patch['path']
        if hashlib.sha256(path.read_bytes()).hexdigest()!=patch['sha256']: raise ContractError('patch_identity',str(path))
        command(['git','apply','--check',str(path)],source,log)
        command(['git','apply',str(path)],source,log)
    if command(['git','status','--porcelain','--untracked-files=no'],cache/'libmonome'):
        raise ContractError('dirty_dependency','libmonome has modified source; preserving checkout')
    command(['python3','waf','configure','--prefix='+str(prefix),'--enable-embedded-protos'],cache/'libmonome',log)
    command(['python3','waf','build','install','-j8'],cache/'libmonome',log)
    env=dict(os.environ,CFLAGS='-I'+str(prefix/'include')+' -Wno-error=unused-result',LDFLAGS='-L'+str(prefix/'lib'))
    command(['python3','waf','configure','--desktop'],source,log,env)
    command(['python3','waf','build','--targets=matron,crone','-j8'],source,log,env)
    binaries={}
    for name,path in [('matron',source/'build/matron/matron'),('crone',source/'build/crone/crone'),('libmonome',prefix/'lib/libmonome.so')]:
        binaries[name]=dict(path=str(path),sha256=hashlib.sha256(path.read_bytes()).hexdigest())
    install=dict(lock_sha256=digest,source=str(source),prefix=str(prefix),binaries=binaries,
                 norns_revision=lock['dependencies']['norns']['commit'],patches=lock['patches'],interpreted_files=runtime_content(source))
    write_json(directory/'installation.json',install); write_json(ROOT/'.runtime/current.json',install)
    return install
