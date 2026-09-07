"""Prepare an explicit isolated Mosaic bug-fix candidate; baseline stays intact."""
import hashlib,json,os,shutil,subprocess,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from automation.protocol import ROOT,ContractError,read_json,write_json
from automation.identity import application_identity

def prepare(spec_path=None):
    spec_path=spec_path or ROOT/'fixtures/apps/mosaic-patches/manifest.json';spec=read_json(spec_path)
    lock=read_json(ROOT/'fixtures/apps/mosaic.lock.json')
    if spec['base_revision']!=lock['sources']['mosaic']['commit']:raise ContractError('candidate_base','Candidate base does not match fixture lock')
    base=ROOT/'.runtime/fixtures/mosaic/code/mosaic'
    def git(args,cwd):
        env=os.environ.copy()
        if args[0]=='apply':
            # Owned copies have no .git. Do not discover the enclosing emulator
            # repository and silently filter git-format paths as out of scope.
            env['GIT_CEILING_DIRECTORIES']=str(cwd.parent)
        return subprocess.check_output(['git',*args],cwd=cwd,env=env,text=True).strip()
    if git(['rev-parse','HEAD'],base)!=spec['base_revision'] or git(['status','--porcelain','--untracked-files=no'],base):
        raise ContractError('candidate_base','Pinned baseline changed; preserve and inspect it')
    for item in spec['files']:
        path=ROOT/item['path']
        if hashlib.sha256(path.read_bytes()).hexdigest()!=item['sha256']:raise ContractError('candidate_patch','Candidate patch/test content differs from manifest')
    digest=hashlib.sha256(spec_path.read_bytes()).hexdigest()
    directory=ROOT/'.runtime/candidates/mosaic'/digest[:16];code=directory/'code';record=directory/'candidate.json'
    if directory.exists():
        if not record.exists():raise ContractError('incomplete_candidate','Inspect incomplete candidate '+str(directory))
        known=read_json(record)
        if known['manifest_sha256']!=digest or known['application']['digest']!=application_identity(code)['digest']:
            raise ContractError('changed_candidate','Candidate source changed; preserving '+str(directory))
        return code
    code.mkdir(parents=True)
    shutil.copytree(base,code/'mosaic',ignore=shutil.ignore_patterns('.git','test_artefacts','__pycache__'))
    for item in spec['files']:
        path=ROOT/item['path']
        if item['kind']=='patch':
            before=application_identity(code)['digest']
            git(['apply','--check',str(path)],code/'mosaic');git(['apply',str(path)],code/'mosaic')
            if application_identity(code)['digest']==before:raise ContractError('candidate_patch_noop','Patch did not change candidate content')
            git(['apply','--reverse','--check',str(path)],code/'mosaic')
        elif item['kind']=='test':shutil.copyfile(path,code/'mosaic/lib/tests/lib/emulator_memory_regression_tests.lua')
        else:raise ContractError('candidate_kind','Unknown candidate file kind')
    write_json(record,dict(base_revision=spec['base_revision'],manifest_sha256=digest,patch_set=spec['name'],files=spec['files'],application=application_identity(code)))
    return code

if __name__=='__main__':print(prepare())
