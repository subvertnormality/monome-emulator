"""One ordinary launcher session, with explicitly owned persistent container data."""
import argparse
import fcntl
import json
import os
from pathlib import Path
import re
import signal
import sys
import threading

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'src'))
from automation import session
from automation.datasets import mapping, MARKER as DATASET_MARKER
from automation.protocol import ContractError, read_json, write_json

class DataRoot:
    MARKER = '.emu-container.json'
    LOCK = '.emu-container.lock'

    def __init__(self, root, script, code_root):
        self.root = Path(root).resolve()
        self.fd = None
        self.root.mkdir(parents=True, exist_ok=True)
        marker = self.root/self.MARKER
        expected = mapping(dict(script=script, code_root=code_root))
        fresh = not marker.exists()
        if fresh and any(self.root.iterdir()):
            raise ContractError('container_data_unowned', 'Data root is nonempty and has no container ownership marker')
        try:
            self.fd = os.open(self.root/self.LOCK, os.O_RDWR | os.O_NOFOLLOW |
                              (os.O_CREAT | os.O_EXCL if fresh else 0), 0o600)
            try:
                fcntl.flock(self.fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError as error:
                raise ContractError('container_data_busy', 'Another container owns this data root') from error
            if fresh:
                self.value = dict(schema_version=1, mapping=expected, dataset=None)
                write_json(marker, self.value)
            else:
                if marker.is_symlink():
                    raise ContractError('container_data_metadata', 'Container marker must not be a symlink')
                self.value = read_json(marker)
                if (not isinstance(self.value, dict) or set(self.value) != {'schema_version', 'mapping', 'dataset'}
                        or self.value['schema_version'] != 1):
                    raise ContractError('container_data_metadata', 'Unsupported container data marker')
                if self.value['mapping'] != expected:
                    raise ContractError('container_data_mapping', 'Data root belongs to a different application mapping')
                dataset = self.value['dataset']
                if dataset is not None and (not isinstance(dataset, str) or not re.fullmatch('[0-9a-f]{32}', dataset)):
                    raise ContractError('container_data_metadata', 'Invalid dataset directory identity')
                if dataset is not None and (self.root/dataset).is_symlink():
                    raise ContractError('container_data_metadata', 'Dataset directory must not be a symlink')
        except Exception:
            self.close()
            raise

    def options(self):
        dataset = self.value['dataset']
        return dict(reopen_data=self.root/dataset) if dataset else dict(data=self.root)

    def remember(self, session_id):
        if self.value['dataset'] is None and re.fullmatch('[0-9a-f]{32}', session_id):
            dataset = self.root/session_id
            if (dataset/DATASET_MARKER).is_file():
                self.value['dataset'] = session_id
                write_json(self.root/self.MARKER, self.value)

    def close(self):
        if self.fd is not None:
            os.close(self.fd)
            self.fd = None

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--script', type=Path, default=ROOT/'fixtures/probes/probe-a/probe-a.lua')
    parser.add_argument('--code-root', type=Path)
    parser.add_argument('--data-root', type=Path, default=Path('/data'))
    parser.add_argument('--port', type=int, default=8765)
    args = parser.parse_args()
    stopped = threading.Event()
    for sig in (signal.SIGTERM, signal.SIGINT):
        signal.signal(sig, lambda *_: stopped.set())
    owner = DataRoot(args.data_root, args.script, args.code_root)
    info = None
    try:
        try:
            info = session.start(backend='native', script=args.script, code_root=args.code_root,
                experimental_install=ROOT/'.runtime/container-audio-tools/installation.json',
                crow_enabled=False, startup_chime=False, listen_address='0.0.0.0', http_port=args.port,
                **owner.options())
        except Exception as error:
            if getattr(error, 'session_id', None):
                owner.remember(error.session_id)
            raise
        owner.remember(info['session_id'])
        write_json(owner.root/'.emu-container-current.json', info)
        print(json.dumps(dict(status='ready', **info)), flush=True)
        while not stopped.wait(.2):
            if (session.SESSIONS/info['session_id']/'stopped.json').exists():
                break
            # Surface unexpected server loss, rather than an apparently live container.
            os.kill(info['pid'], 0)
    finally:
        try:
            if info is not None:
                session.stop(info['session_id'])
                print(json.dumps(dict(status='stopped', session_id=info['session_id'])), flush=True)
        finally:
            owner.close()

if __name__ == '__main__':
    main()
