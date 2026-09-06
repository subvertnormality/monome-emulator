"""Content identities include uncommitted implementation files, not just HEAD."""
import hashlib
import json
from pathlib import Path
import subprocess
from .protocol import ROOT, ContractError

def artifact(path,base):
    path=Path(path).resolve(); base=Path(base).resolve()
    try: relative=path.relative_to(base)
    except ValueError: raise ContractError('path_escape','Artifact escapes its evidence directory')
    if not path.is_file(): raise ContractError('missing_artifact',str(relative))
    data=path.read_bytes()
    return dict(path=relative.as_posix(),sha256=hashlib.sha256(data).hexdigest(),size=len(data))

def source_identity():
    files=[]
    for name in ['src','dev','scripts','schemas','patches','compatibility','fixtures','tests']:
        for p in (ROOT/name).rglob('*'):
            if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.pyc': files.append(artifact(p,ROOT))
    files.append(artifact(ROOT/'dependencies.lock.json',ROOT))
    files.sort(key=lambda f:f['path'])
    digest=hashlib.sha256(json.dumps(files,sort_keys=True).encode()).hexdigest()
    revision=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    return dict(revision=revision,digest=digest,files=files)

def verify_artifact(record,base):
    actual=artifact(Path(base)/record['path'],base)
    if actual!=record: raise ContractError('artifact_changed',record['path'])

def application_identity(code_root):
    import os
    base=Path(code_root).absolute(); files=[]; seen=set()
    for current,dirs,names in os.walk(base,followlinks=True):
        real=Path(current).resolve()
        if real in seen: dirs[:]=[]; continue
        seen.add(real)
        dirs[:]=[d for d in dirs if d not in ('.git','node_modules','__pycache__','test_artefacts')]
        for name in sorted(names):
            p=Path(current)/name
            if not p.is_file() or name.endswith('.pyc'): continue
            content=p.read_bytes()
            files.append(dict(path=p.relative_to(base).as_posix(),sha256=hashlib.sha256(content).hexdigest(),size=len(content)))
    files.sort(key=lambda f:f['path'])
    if not files: raise ContractError('empty_application','No application source files')
    return dict(code_root=str(base),digest=hashlib.sha256(json.dumps(files,sort_keys=True).encode()).hexdigest(),files=files)
