"""Public Python client for external behaviour suites; no application knowledge."""
import shutil
from pathlib import Path
from . import session
from .protocol import ContractError,uid,write_json

class Session:
    """Own one native session. Call close even when an assertion fails."""
    def __init__(self,*,script,code_root,data=None,data_seeds=None,midi_config=None,
                 enabled_mods=None,random_seed=None,clock_mode='real-time',experimental_install=None,crow_enabled=True,audio_files=None,audio_directory=None,input_timeout=2,arc_enabled=False,desktop_audio=None,startup_chime=True,reopen_data=None,maiden_install=None,listen_address='127.0.0.1',http_port=0,jack_period=1024):
        self.info=session.start('native',script=script,code_root=code_root,data=data,
            data_seeds=data_seeds,midi_config=midi_config,enabled_mods=enabled_mods,
            random_seed=random_seed,clock_mode=clock_mode,experimental_install=experimental_install,crow_enabled=crow_enabled,audio_files=audio_files,audio_directory=audio_directory,input_timeout=input_timeout,arc_enabled=arc_enabled,desktop_audio=desktop_audio,startup_chime=startup_chime,reopen_data=reopen_data,maiden_install=maiden_install,listen_address=listen_address,http_port=http_port,jack_period=jack_period)
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
    def capture_start(self,seconds,*,input=None):
        """Start a finite WAV capture, optionally injecting a session-data WAV."""
        payload=dict(seconds=seconds)
        if input is not None:payload['input']=input
        return session.request(self.id,'/audio/capture/start',payload)
    def capture_status(self,job_id):
        return session.request(self.id,'/audio/capture/status',dict(job_id=job_id))
    def capture_cancel(self,job_id):
        return session.request(self.id,'/audio/capture/cancel',dict(job_id=job_id))
    def crow_capture_start(self,seconds):
        return session.request(self.id,'/crow/capture/start',dict(seconds=seconds))
    def crow_input(self,channel,volts):
        return session.request(self.id,'/crow/input',dict(channel=channel,volts=volts))
    def crow_ii_read(self,cursor=0):
        """Read up to 256 wire packets; pass returned byte cursor for the next page."""
        return session.request(self.id,'/crow/ii/read',dict(cursor=cursor))
    def crow_capture_status(self,job_id):
        return session.request(self.id,'/crow/capture/status',dict(job_id=job_id))
    def crow_capture_cancel(self,job_id):
        return session.request(self.id,'/crow/capture/cancel',dict(job_id=job_id))
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
            if (source/'audio-captures').exists():
                shutil.copytree(source/'audio-captures',directory/'audio-captures')
            if (source/'crow-captures').exists():
                shutil.copytree(source/'crow-captures',directory/'crow-captures')
            write_json(directory/'identity.json',{k:v for k,v in self.info.items() if k in (
                'session_id','runtime_identity','application_identity','emulator_identity','audio_identity','crow_enabled','input_timeout','arc_enabled','startup_chime','desktop_audio')})
