"""Container data ownership and shared launcher binding regressions."""
import importlib.util
import json
from pathlib import Path
import socket
import tempfile
import unittest
from automation import session
from automation.protocol import ContractError, ROOT

spec=importlib.util.spec_from_file_location('container_entry', ROOT/'scripts/container/entrypoint.py')
entry=importlib.util.module_from_spec(spec);spec.loader.exec_module(entry)

class ContainerContracts(unittest.TestCase):
    def test_data_ownership_restart_and_isolation(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary)/'data'
            first=entry.DataRoot(root, '/code/probe/main.lua', '/code')
            try:
                self.assertEqual(first.options(),dict(data=root))
                with self.assertRaisesRegex(ContractError, 'Another container'):
                    entry.DataRoot(root, '/code/probe/main.lua', '/code')
                dataset='a'*32
                (root/dataset).mkdir()
                (root/dataset/entry.DATASET_MARKER).write_text('{}')
                (root/dataset/'user.txt').write_text('keep')
                first.remember(dataset)
            finally:first.close()
            second=entry.DataRoot(root, '/code/probe/main.lua', '/code')
            try:self.assertEqual(second.options(),dict(reopen_data=root/dataset))
            finally:second.close()
            self.assertEqual((root/dataset/'user.txt').read_text(),'keep')
            with self.assertRaisesRegex(ContractError, 'different application'):
                entry.DataRoot(root, '/code/other/main.lua', '/code')
            other=entry.DataRoot(Path(temporary)/'other','/code/probe/main.lua','/code')
            try:self.assertIn('data',other.options())
            finally:other.close()

    def test_unowned_and_invalid_dataset_refused(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary)
            (root/'user.txt').write_text('keep')
            with self.assertRaisesRegex(ContractError,'nonempty'):
                entry.DataRoot(root,'/code/probe/main.lua','/code')
            self.assertEqual(list(root.iterdir()),[root/'user.txt'])
            owned=root/'owned';owner=entry.DataRoot(owned,'/code/probe/main.lua','/code');owner.close()
            value=json.loads((owned/entry.DataRoot.MARKER).read_text());value['dataset']='../outside'
            (owned/entry.DataRoot.MARKER).write_text(json.dumps(value))
            with self.assertRaisesRegex(ContractError,'Invalid dataset'):
                entry.DataRoot(owned,'/code/probe/main.lua','/code')

    def test_bind_defaults_fixed_port_and_collision(self):
        default=session.start()
        try:
            self.assertEqual(default['listen_address'],'127.0.0.1')
            self.assertEqual(session.request(default['session_id'],'/health')['status'],'ready')
            with self.assertRaises(ContractError) as failed:
                session.start(listen_address='0.0.0.0',http_port=default['port'])
            self.assertIn('Address already in use',str(failed.exception))
            self.assertEqual(session.request(default['session_id'],'/health')['status'],'ready')
        finally:session.stop(default['session_id'])
        fixed=session.start(listen_address='0.0.0.0',http_port=default['port'])
        try:
            self.assertEqual(fixed['port'],default['port'])
            self.assertEqual(session.request(fixed['session_id'],'/health')['status'],'ready')
        finally:session.stop(fixed['session_id'])

    def test_invalid_binding_rejected_before_session_creation(self):
        before=set(session.SESSIONS.iterdir())
        for options in [dict(http_port=True),dict(http_port=-1),dict(http_port=65536),
                        dict(listen_address='example.com'),dict(http_port=8765,maiden_install='unused')]:
            with self.assertRaises(ContractError):session.start(**options)
        self.assertEqual(set(session.SESSIONS.iterdir()),before)

if __name__=='__main__':unittest.main()
