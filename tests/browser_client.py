"""Drive the pinned Windows browser from a WSL-native workflow test process."""
import json,selectors,subprocess
from automation.protocol import ROOT,ContractError

def windows_path(path):
    value=str(path)
    if not value.startswith('/mnt/c/'):raise ValueError('Windows browser requires a shared C: artifact path')
    return 'C:/'+value[len('/mnt/c/'):]

class Browser:
    def __init__(self,url,directory):
        self.log=open(directory/'browser-driver.log','w')
        self.proc=subprocess.Popen(['/mnt/c/Users/andy/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node.exe',windows_path(ROOT/'tests/browser_driver.cjs')],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=self.log,text=True)
        self.request(dict(open=url))
    def request(self,value):
        self.proc.stdin.write(json.dumps(value)+'\n');self.proc.stdin.flush()
        with selectors.DefaultSelector() as selector:
            selector.register(self.proc.stdout,selectors.EVENT_READ)
            if not selector.select(30):raise ContractError('browser_timeout','Browser input driver did not acknowledge within 30 seconds')
        result=json.loads(self.proc.stdout.readline())
        if not result['ok']:raise ContractError('browser_action',result['error'])
    def close(self):
        try:
            if self.proc.poll() is None:self.request(dict(close=True));self.proc.wait(timeout=5)
        finally:
            if self.proc.poll() is None:self.proc.kill();self.proc.wait(timeout=5)
            self.log.close()
