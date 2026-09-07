"""Channel defaults versus step-specific masks, verified by emitted MIDI."""
import time
from mosaic_workflows import run_package
from mosaic_channels import notes,silence

def held_delta(c,step,delta):
    c.action(type='grid',x=step,y=4,state=1)
    try:time.sleep(.05);c.enc(3,delta)
    finally:c.action(type='grid',x=step,y=4,state=0)
    time.sleep(.1)

def global_masks(c):
    c.configure();c.enc(1,-4);c.screen_header('Ch. 1 Note Masks')
    c.enc(2,1);c.enc(3,81) # unset -1 -> channel velocity 80
    c.playback([(1,[144,n,80]) for n in (60,62,64,65)]);c.passed('channel-velocity-default')
    held_delta(c,2,30)
    c.playback([(1,[144,n,v]) for n,v in [(60,80),(62,110),(64,80),(65,80)]])
    c.passed('step-velocity-precedence')
    c.enc(2,-1);c.enc(3,56) # unset -1 -> MIDI G3, 55
    c.playback([(1,[144,55,v]) for v in (80,110,80,80)]);c.passed('channel-note-default')
    held_delta(c,3,14)
    c.playback([(1,[144,n,v]) for n,v in [(55,80),(55,110),(69,80),(55,80)]])
    c.passed('step-note-precedence')
    c.enc(2,-1);c.enc(3,1) # unset -1 -> channel trig off
    silence(c);c.passed('channel-trig-off')
    held_delta(c,2,1) # step overrides channel off
    c.playback([(1,[144,55,110])]);c.passed('step-trig-overrides-channel-off')
    c.action(type='key',n=1,state=1)
    try:time.sleep(.3);c.key(2)
    finally:c.action(type='key',n=1,state=0)
    c.playback(notes());c.passed('clear-defaults-and-step-overrides')

if __name__=='__main__':
    import sys
    from automation.protocol import ROOT
    from mosaic_candidate import prepare
    candidate='--candidate' in sys.argv
    code=prepare(ROOT/'fixtures/apps/mosaic-patches/midi-counts.json') if candidate else None
    run_package('A06-channel-mask-precedence' if candidate else 'A06-channel-mask-precedence-baseline',global_masks,code)
