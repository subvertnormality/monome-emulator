import sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'scripts'))
from proc_thread_sampler import ThreadSampler,process_stat

def stat(pid,parent,start):
    fields=['S',str(parent)]+['0']*17+[str(start)]
    return str(pid)+' (name with (parentheses)) '+' '.join(fields)

class ThreadSamples(unittest.TestCase):
    def test_stat_parses_names_without_shifting_fields(self):
        self.assertEqual(process_stat(stat(5,3,123)),dict(state='S',parent=3,start_ticks=123))

    def test_only_descendants_and_no_reused_pid(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            for pid,parent in [(1,0),(2,1),(3,2),(4,1)]:
                base=root/str(pid);task=base/'task'/str(pid);task.mkdir(parents=True)
                (base/'comm').write_text('matron' if pid in (3,4) else 'python')
                for p in (base/'stat',task/'stat'):p.write_text(stat(pid,parent,pid*100))
                (task/'comm').write_text('probe');(task/'wchan').write_text('wait')
                (task/'schedstat').write_text('100 20 3')
            sampler=ThreadSampler(2,root);value=sampler.sample()
            self.assertEqual({r['pid'] for r in value['threads']},{2,3})
            self.assertIsNone(sampler.schedstats_enabled)
            filtered=ThreadSampler(2,root,process_name='matron')
            self.assertEqual({r['pid'] for r in filtered.sample()['threads']},{3})
            (root/'3/stat').write_text(stat(3,1,999))
            self.assertEqual({r['pid'] for r in sampler.sample()['threads']},{2})

if __name__=='__main__':unittest.main()
