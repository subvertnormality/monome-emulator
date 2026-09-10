import os,tempfile,threading,time,unittest
from pathlib import Path
from automation.protocol import ContractError
from runtime.startup_lock import StartupLock,lock_path

class StartupLockTests(unittest.TestCase):
    def test_second_holder_waits_for_release(self):
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/'lock';order=[]
            first=StartupLock(path=path).__enter__()
            def second():
                with StartupLock(path=path) as lock:order.append(('second',lock.waited_seconds))
            thread=threading.Thread(target=second);thread.start()
            time.sleep(.3);order.append(('first-release',None));first.__exit__(None,None,None)
            thread.join(5)
            self.assertEqual([name for name,_ in order],['first-release','second'])
            self.assertGreaterEqual(order[1][1],.25)

    def test_timeout_is_a_named_failure_and_releases_the_descriptor(self):
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/'lock'
            with StartupLock(path=path):
                blocked=StartupLock(timeout=.2,path=path)
                with self.assertRaises(ContractError) as caught:blocked.__enter__()
                self.assertEqual(caught.exception.code,'startup_lock_timeout')
                self.assertIsNone(blocked.fd)
            with StartupLock(timeout=.2,path=path) as lock:self.assertLess(lock.waited_seconds,.2)

    def test_lock_is_per_user_host_wide_unless_overridden(self):
        previous=os.environ.pop('NORNS_EMU_STARTUP_LOCK',None)
        try:
            self.assertEqual(lock_path(),Path('/tmp/norns-emulator-%d-startup.lock'%os.getuid()))
            os.environ['NORNS_EMU_STARTUP_LOCK']='/tmp/x.lock'
            self.assertEqual(lock_path(),Path('/tmp/x.lock'))
        finally:
            os.environ.pop('NORNS_EMU_STARTUP_LOCK',None)
            if previous is not None:os.environ['NORNS_EMU_STARTUP_LOCK']=previous

if __name__=='__main__':unittest.main()
