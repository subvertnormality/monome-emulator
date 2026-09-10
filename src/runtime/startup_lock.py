"""Host-wide, per-user serialisation of native audio-server startup.

Every session starts its own named JACK server, but all JACK servers for a user
share one shared-memory registry. Measured on WSL (tests/concurrent_session_
startup.py): six sessions started at the same instant failed 15 of 18 times with
crone aborts and matron exits while registering JACK clients. Holding this lock
from JACK launch until the script is ready makes concurrent starts sequential.
The lock is per user and per host, not per checkout, because the registry is.
"""
import fcntl,os,time
from pathlib import Path

from automation.protocol import ContractError

DEFAULT_TIMEOUT=180

def lock_path():
    override=os.environ.get('NORNS_EMU_STARTUP_LOCK')
    return Path(override) if override else Path('/tmp')/('norns-emulator-%d-startup.lock'%os.getuid())

class StartupLock:
    def __init__(self,timeout=DEFAULT_TIMEOUT,path=None):
        self.timeout=timeout;self.path=Path(path) if path else lock_path()
        self.fd=None;self.waited_seconds=None
    def __enter__(self):
        self.fd=os.open(str(self.path),os.O_RDWR|os.O_CREAT,0o600)
        started=time.monotonic()
        while True:
            try:
                fcntl.flock(self.fd,fcntl.LOCK_EX|fcntl.LOCK_NB);break
            except BlockingIOError:
                if time.monotonic()-started>=self.timeout:
                    os.close(self.fd);self.fd=None
                    raise ContractError('startup_lock_timeout',
                        'Another native session held the startup lock for over %ss: %s'%(self.timeout,self.path))
                time.sleep(0.05)
        self.waited_seconds=round(time.monotonic()-started,3)
        return self
    def __exit__(self,*exc):
        if self.fd is not None:
            fcntl.flock(self.fd,fcntl.LOCK_UN);os.close(self.fd);self.fd=None
        return False
