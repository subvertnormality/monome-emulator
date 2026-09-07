"""Run a diagnostic command with an independent process scheduling heartbeat.

No timing result is waived. Child exit status propagates. Samples stay in memory
during execution so heartbeat measurements do not wait on artifact filesystem I/O.
"""
import argparse,json,os,platform,subprocess,time,uuid
from pathlib import Path

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--threads',action='store_true',help='Sample Linux descendant thread CPU/wait counters')
    parser.add_argument('--thread-process',help='Restrict thread sampling to this exact descendant process name')
    parser.add_argument('command',nargs=argparse.REMAINDER)
    args=parser.parse_args();command=args.command
    if command[:1]==['--']:command=command[1:]
    if not command:parser.error('Supply a command after --')
    if args.thread_process and not args.threads:parser.error('--thread-process requires --threads')
    args.output.mkdir(parents=True,exist_ok=False)
    samples=[];thread_samples=[];period=.01;started=time.monotonic_ns();sampler=None
    with (args.output/'command.log').open('w') as log:
        child=subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT)
        if args.threads:
            from proc_thread_sampler import ThreadSampler
            sampler=ThreadSampler(child.pid,process_name=args.thread_process)
        while child.poll() is None:
            samples.append([time.monotonic_ns(),time.process_time_ns()])
            if sampler:thread_samples.append(sampler.sample())
            time.sleep(period)
        code=child.wait()
    samples.append([time.monotonic_ns(),time.process_time_ns()])
    gaps=[(b[0]-a[0])/1e6 for a,b in zip(samples,samples[1:])]
    result=dict(kind='host-timing-diagnostic',schema_version=1,command=command,
        host=dict(platform=platform.platform(),release=platform.release()),exit_code=code,
        started_ns=started,finished_ns=time.monotonic_ns(),period_ms=10,
        maximum_sample_gap_ms=max(gaps,default=0),samples=samples,
        acceptance_waiver=False)
    if sampler:
        (args.output/'threads.json').write_text(json.dumps(dict(
            schedstats_enabled=sampler.schedstats_enabled,samples=thread_samples))+'\n')
    (args.output/'heartbeat.json').write_text(json.dumps(result)+'\n')
    print(args.output/'heartbeat.json',flush=True)
    return code

if __name__=='__main__':raise SystemExit(main())
