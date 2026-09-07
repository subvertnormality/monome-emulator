"""Mask overrides and their removal, with independent emitted-note expectations."""
import time
from mosaic_workflows import run_package
from mosaic_channels import notes
from mosaic_memory import mask

def clear_step(c,x):
    c.action(type='grid',x=x,y=4,state=1)
    try:time.sleep(.05);c.key(2)
    finally:c.action(type='grid',x=x,y=4,state=0)
    time.sleep(.1)

def masks(c):
    c.configure();c.enc(1,-4);c.screen_header('Ch. 1 Note Masks')
    c.playback(notes());c.passed('underlying-pattern')
    c.shift_tap(2,4);c.led_values([(2,4)],[2]);c.playback([notes()[i] for i in (0,2,3)])
    c.passed('step-trig-mask-silences')
    c.shift_tap(2,4);c.playback(notes());c.passed('step-trig-mask-restores')
    mask(c,1,72);mask(c,3,69)
    c.playback([(1,[144,n,v]) for n,v in [(72,127),(62,117),(69,107),(65,97)]])
    c.passed('independent-step-note-masks')
    clear_step(c,1)
    c.playback([(1,[144,n,v]) for n,v in [(60,127),(62,117),(69,107),(65,97)]])
    c.passed('remove-one-preserves-other')
    c.action(type='key',n=1,state=1)
    try:time.sleep(.3);c.key(2)
    finally:c.action(type='key',n=1,state=0)
    c.playback(notes());c.screen_header('Ch. 1 Note Masks');c.passed('clear-channel-restores-pattern')
    clear_step(c,1);c.playback(notes());c.passed('clear-empty-step-is-idempotent')

if __name__=='__main__':run_package('A06-mask-removal-controls',masks)
