"""Explicit launcher-owned datasets; process-held single-writer ownership."""
import json,os,re
from pathlib import Path
from .protocol import ContractError,uid

MARKER='.emu-dataset.json'
LOCK='.emu-dataset.lock'
SYSTEM_FILES=('system.state','system.mods','system.kbd_layout')

def mapping(config):
    if not config.get('script'):raise ContractError('script_required','Select an external script with --script')
    entry=Path(config['script']).resolve()
    root=Path(config['code_root']).resolve() if config.get('code_root') else entry.parent.parent
    try:relative=entry.relative_to(root)
    except ValueError:raise ContractError('dataset_mapping','Script is outside the selected code root')
    return dict(code_root=str(root),entry=relative.as_posix())

class Lease:
    def __init__(self,config):
        import fcntl
        self.fd=None;root=Path(config['data']);marker=root/MARKER
        expected=mapping(config);reopen=config.get('reopen_data',False)
        if reopen:
            if marker.is_symlink() or not marker.is_file():raise ContractError('dataset_unowned','Reopen requires a launcher-owned dataset marker')
            try:metadata=json.loads(marker.read_text())
            except (OSError,ValueError) as error:raise ContractError('dataset_metadata',str(error)) from error
            if not isinstance(metadata,dict) or set(metadata)!={'schema_version','dataset_id','mapping'} or metadata['schema_version']!=1:
                raise ContractError('dataset_metadata','Unsupported dataset metadata')
            if not isinstance(metadata['dataset_id'],str) or not re.fullmatch('[0-9a-f]{32}',metadata['dataset_id']):
                raise ContractError('dataset_metadata','Invalid dataset identity')
            if metadata['mapping']!=expected:raise ContractError('dataset_mapping','Dataset belongs to a different application mapping')
        else:metadata=dict(schema_version=1,dataset_id=uid(),mapping=expected)
        try:
            self.fd=os.open(root/LOCK,os.O_RDWR|os.O_NOFOLLOW|(0 if reopen else os.O_CREAT|os.O_EXCL),0o600)
            try:fcntl.flock(self.fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
            except BlockingIOError as error:raise ContractError('dataset_busy','Another session owns this writable dataset') from error
            for name in SYSTEM_FILES:
                if (root/name).is_symlink():raise ContractError('dataset_system_file','Refusing a linked startup file: '+name)
            if not reopen:
                with marker.open('x') as file:json.dump(metadata,file,indent=2);file.write('\n')
            config['dataset']=metadata
        except Exception:
            self.close();raise
    def close(self):
        if self.fd is not None:os.close(self.fd);self.fd=None
