"""Bounded real-time beat observation; never advances or replaces native clocks."""
import time
from .protocol import ContractError

class Timeline:
    def __init__(self,observe,deadline):
        self.observe=observe;self.deadline=deadline;self.anchors={};self.events=[]
    def sample(self):
        observation=self.observe()
        if observation['backend']!='native':raise ContractError('clock_fidelity','Beat waits require a native runtime')
        values=observation['state'].get('diagnostics',{})
        if not {'beats','tempo','clock_epoch','monotonic_ns'}<=set(values):raise ContractError('clock_observation','Native clock observation is incomplete')
        return dict(beats=values['beats'],tempo=values['tempo'],epoch=values['clock_epoch'],monotonic_ns=values['monotonic_ns'])
    def anchor(self,name):
        if name in self.anchors:raise ContractError('duplicate_anchor','Beat anchor already exists: '+name)
        value=self.sample();self.anchors[name]=value
        self.events.append(dict(kind='anchor',name=name,observation=value))
    def wait(self,spec,kind='wait_beats'):
        if spec['anchor'] not in self.anchors:raise ContractError('missing_anchor','Unknown beat anchor: '+spec['anchor'])
        anchor=self.anchors[spec['anchor']];target=anchor['beats']+spec['beats']
        end=min(self.deadline,time.monotonic()+spec['timeout_ms']/1000)
        while True:
            if time.monotonic()>=end:raise ContractError('beat_timeout','Native clock did not reach anchor '+spec['anchor']+' + '+str(spec['beats'])+' beats')
            current=self.sample()
            if current['epoch']!=anchor['epoch']:raise ContractError('clock_reset','Native transport restarted after beat anchor; establish a new anchor')
            if current['beats']>=target:
                self.events.append(dict(kind=kind,name=spec['anchor'],target_beats=target,observation=current))
                return
            time.sleep(min(.005,max(0,end-time.monotonic())))
