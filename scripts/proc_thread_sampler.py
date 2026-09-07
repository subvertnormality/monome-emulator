"""Read-only Linux thread samples for descendants of one diagnostic command."""
from pathlib import Path
import time

def process_stat(text):
    # comm may contain spaces or parentheses; remaining fields start at state.
    end=text.rfind(')');fields=text[end+2:].split()
    return dict(state=fields[0],parent=int(fields[1]),start_ticks=int(fields[19]))

class ThreadSampler:
    def __init__(self,parent,proc=Path('/proc'),process_name=None):
        self.parent=parent;self.proc=proc;self.selected={};self.next_scan=0
        self.process_name=process_name
        setting=proc/'sys/kernel/sched_schedstats'
        self.schedstats_enabled=setting.read_text().strip()=='1' if setting.exists() else None

    def discover(self):
        processes={}
        for path in self.proc.iterdir():
            if not path.name.isdigit():continue
            try:processes[int(path.name)]=process_stat((path/'stat').read_text())
            except (FileNotFoundError,ProcessLookupError,PermissionError):continue
        selected={}
        for pid,info in processes.items():
            ancestor=pid;seen=set()
            while ancestor in processes and ancestor not in seen:
                if ancestor==self.parent:
                    try:
                        if self.process_name is None or (self.proc/str(pid)/'comm').read_text().strip()==self.process_name:
                            selected[pid]=info['start_ticks']
                    except (FileNotFoundError,ProcessLookupError):pass
                    break
                seen.add(ancestor);ancestor=processes[ancestor]['parent']
        self.selected=selected

    def sample(self):
        now=time.monotonic_ns()
        if now>=self.next_scan:self.discover();self.next_scan=now+500_000_000
        rows=[]
        for pid,start in self.selected.items():
            base=self.proc/str(pid)
            try:
                if process_stat((base/'stat').read_text())['start_ticks']!=start:continue
                for thread in (base/'task').iterdir():
                    try:
                        sampled_ns=time.monotonic_ns()
                        stat=process_stat((thread/'stat').read_text())
                        counters=[int(n) for n in (thread/'schedstat').read_text().split()]
                        rows.append(dict(pid=pid,tid=int(thread.name),start_ticks=stat['start_ticks'],sampled_ns=sampled_ns,
                            name=(thread/'comm').read_text().strip(),state=stat['state'],
                            cpu_ns=counters[0],runnable_wait_ns=counters[1],timeslices=counters[2],
                            wait_channel=(thread/'wchan').read_text().strip()))
                    except (FileNotFoundError,ProcessLookupError):continue
            except (FileNotFoundError,ProcessLookupError):continue
        return dict(started_ns=now,finished_ns=time.monotonic_ns(),threads=rows)
