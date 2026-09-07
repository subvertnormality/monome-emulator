"""Mask edits and history traversal through actual keys, grid and encoders."""
import time
from mosaic_workflows import run_package

BASE=[(1,[144,n,v]) for n,v in [(60,127),(62,117),(64,107),(65,97)]]
MASKED=[(1,[144,n,v]) for n,v in [(72,127),(62,117),(69,107),(65,97)]]
ONE=[(1,[144,n,v]) for n,v in [(72,127),(62,117),(64,107),(65,97)]]

def mask(c,step,note):
    c.action(type='grid',x=step,y=4,state=1)
    try:
        # Native Mosaic refreshes the held step selector on its scheduler.
        time.sleep(.05);c.enc(3,note+1)
    finally:c.action(type='grid',x=step,y=4,state=0)
    time.sleep(.1)

def memory(c):
    c.configure();c.enc(1,-4);c.screen_header('Ch. 1 Note Masks')
    c.playback(BASE);c.passed('baseline-pattern')
    mask(c,1,72);mask(c,3,69)
    c.playback(MASKED);c.passed('two-mask-edits')
    c.enc(1,2);c.screen_header('Ch. 1 Memory')
    c.enc(3,-1);c.playback(ONE);c.passed('undo-one')
    c.enc(3,1);c.playback(MASKED);c.passed('redo-one')
    c.key(2);c.playback(BASE);c.passed('undo-all')
    c.key(3);c.playback(MASKED);c.passed('redo-all')
    c.action(type='key',n=1,state=1)
    time.sleep(.3)
    try:c.key(2)
    finally:c.action(type='key',n=1,state=0)
    c.playback(BASE);c.key(3);c.playback(BASE);c.passed('undo-and-forget')
    c.enc(1,-2);mask(c,1,72);mask(c,3,69);c.enc(1,2)
    c.key(2);c.playback(BASE)
    c.action(type='key',n=1,state=1)
    time.sleep(.3)
    try:c.key(3)
    finally:c.action(type='key',n=1,state=0)
    c.playback(MASKED);c.key(2);c.playback(MASKED);c.passed('redo-and-forget')

if __name__=='__main__':
    import sys
    code=None
    if '--candidate' in sys.argv:
        from mosaic_candidate import prepare
        code=prepare()
    run_package('A15-memory-undo-and-redo' if code else 'A15-memory-undo-and-redo-baseline',memory,code)
