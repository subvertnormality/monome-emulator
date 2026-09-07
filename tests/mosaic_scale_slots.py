"""Edit-only versus active scale slots and additive global transposition."""
import time
from mosaic_workflows import run_package

def slots(c):
    c.configure();c.tap(4,8)
    def play(pitches):c.playback([(1,[144,n,v]) for n,v in zip(pitches,[127,117,107,97])])
    play([60,62,64,65]);c.passed('initial-c-major')
    c.shift_tap(16,3);c.screen_header('Scale slot 16 ',selected=1,tabs=3)
    c.enc(2,-1);c.enc(3,2);c.key(3) # root D
    c.enc(2,1);c.enc(3,2);c.key(3) # minor
    # Edit-only selection is dim. The separate stopped active-slot highlight
    # regression is retained for C12 display-refresh acceptance.
    c.led_values([(16,3)],[4]);play([60,62,64,65]);c.passed('shift-edit-does-not-apply')
    c.tap(16,3);c.led_values([(1,3),(16,3)],[2,15]);play([62,64,65,67]);c.passed('activate-last-slot')
    c.action(type='grid',x=1,y=3,state=1)
    try:time.sleep(1.1)
    finally:c.action(type='grid',x=1,y=3,state=0)
    c.screen_header('Scale slot 1 ',selected=1,tabs=3)
    c.led_values([(1,3)],[4]);play([62,64,65,67]);c.passed('hold-edit-does-not-apply')
    c.tap(1,3);play([60,62,64,65]);c.passed('restore-first-slot')
    c.tap(16,3);play([62,64,65,67]);c.passed('slot-edits-retained')
    c.tap(16,8);play([63,65,66,68]);c.passed('global-transpose-increments')
    c.tap(8,8);play([62,64,65,67]);c.passed('global-transpose-decrements')
    # Per-scale +2 remains present when global transposition changes.
    c.enc(2,2);c.enc(3,2);c.key(3);play([64,66,67,69]);c.passed('per-scale-transpose')
    c.tap(15,8);play([76,78,79,81]);c.tap(16,8);play([76,78,79,81]);c.passed('global-upper-bound-adds-to-scale')
    c.tap(9,8);play([52,54,55,57]);c.tap(8,8);play([52,54,55,57]);c.passed('global-lower-bound-adds-to-scale')
    c.tap(12,8);play([64,66,67,69]);c.passed('global-center-restores-scale-offset')

def stopped_highlight(c):
    c.configure();c.tap(4,8)
    c.playback([(1,[144,n,v]) for n,v in zip([60,62,64,65],[127,117,107,97])])
    c.passed('play-and-stop')
    c.shift_tap(16,3);c.led_values([(16,3)],[4]);c.passed('edit-only-indicator')
    c.led_values([(1,3)],[15]);c.passed('stopped-active-highlight')

if __name__=='__main__':
    import sys
    if '--highlight-baseline' in sys.argv:run_package('A19-stopped-scale-highlight-baseline',stopped_highlight)
    else:run_package('A06-scale-slot-controls',slots)
