"""Public Python client for external behaviour suites; no application knowledge."""
import shutil
from pathlib import Path
from . import session
from .protocol import ContractError,uid,write_json

class Session:
    """Own one native session. Call close even when an assertion fails."""
    def __init__(self,*,script,code_root,data=None,data_seeds=None,midi_config=None,
                 enabled_mods=None,random_seed=None):
        self.info=session.start('native',script=script,code_root=code_root,data=data,
            data_seeds=data_seeds,midi_config=midi_config,enabled_mods=enabled_mods,
            random_seed=random_seed)
        self.id=self.info['session_id'];self.sequence=0
    def action(self,action):
        response=session.request(self.id,'/action',dict(schema_version=1,
            session_id=self.id,action_id=uid(),sequence=self.sequence+1,action=action))
        self.sequence+=1
        return response
    def observe(self):
        value=session.request(self.id,'/snapshot')
        if value['errors']:raise ContractError('runtime_errors',str(value['errors']))
        return value
    def capabilities(self):return session.request(self.id,'/capabilities')
    def close(self,artifact_directory):
        """Stop owned processes and export diagnostic evidence, even on failure.

        Never exports session.json/config.json containing local auth credentials.
        Caller owns assertions and its requirement/result manifest.
        """
        directory=Path(artifact_directory)
        try:
            return session.stop(self.id)
        finally:
            directory.mkdir(parents=True,exist_ok=False)
            source=session.SESSIONS/self.id
            for path in source.iterdir():
                if path.suffix in ('.log','.jsonl') or path.name in (
                    'cleanup.json','cleanup-error.json','native-config.json','frame.bgra','stopped.json'):
                    shutil.copyfile(path,directory/path.name)
            write_json(directory/'identity.json',{k:v for k,v in self.info.items() if k in (
                'session_id','runtime_identity','application_identity','emulator_identity')})
