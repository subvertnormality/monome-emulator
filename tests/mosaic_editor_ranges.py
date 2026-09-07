"""Note/velocity range controls and all four groups of sixteen pattern steps."""
import time
from mosaic_workflows import run_package
from mosaic_channels import notes

def hold(c,x,y):
    c.action(type='grid',x=x,y=y,state=1)
    try:time.sleep(1.1)
    finally:c.action(type='grid',x=x,y=y,state=0)

def note_ranges(c):
    c.configure();c.tap(5,8);c.tap(5,8)
    def choose(y,note):
        c.tap(4,y);c.led_values([(4,y)],[12]);c.playback(notes()[:3]+[(1,[144,note,97])])
    choose(1,71);c.passed('initial-note-range')
    c.tap(14,8);choose(1,72);c.passed('first-up-step')
    c.tap(14,8);choose(1,74);c.passed('second-up-step')
    c.tap(16,8);choose(1,72);c.passed('first-down-step')
    c.tap(16,8);choose(1,71);c.passed('second-down-step')
    hold(c,14,8);choose(1,83);c.passed('hold-to-highest-range')
    c.tap(14,8);choose(1,83);c.passed('highest-range-clamp')
    hold(c,16,8);choose(7,48);c.passed('hold-to-lowest-range')
    c.tap(16,8);choose(7,48);c.passed('lowest-range-clamp')
    c.tap(15,8);choose(4,65);c.passed('center-restores-root-page')

VELOCITIES=[127,117,107,97,87,78,68,58,48,39,29,19,9,0]

def velocity_ranges(c):
    c.configure();c.tap(5,8);c.tap(5,8);c.tap(5,8)
    def choose(y,value):
        c.tap(4,y);c.led_values([(4,y)],[12])
        c.playback(notes()[:3]+([(1,[144,65,value])] if value else []))
    for y,value in enumerate(VELOCITIES[:7],1):choose(y,value);c.passed('velocity-'+str(value))
    c.tap(16,8);choose(1,117);c.passed('first-velocity-range-step')
    c.tap(16,8);choose(1,107);c.passed('second-velocity-range-step')
    c.tap(15,8);choose(1,117);c.passed('velocity-range-step-back')
    hold(c,16,8)
    for y,value in enumerate(VELOCITIES[7:],1):choose(y,value);c.passed('velocity-'+str(value))
    c.tap(16,8);choose(7,0);c.passed('lowest-velocity-range-clamp')
    hold(c,15,8);choose(1,127);c.passed('hold-to-highest-velocity-range')
    c.tap(15,8);choose(1,127);c.passed('highest-velocity-range-clamp')

def step_groups(c):
    c.configure();c.tap(5,8)
    for y in range(5,8):
        for x in range(1,5):c.tap(x,y)
    c.tap(5,8)
    for x in range(1,5):c.shift_tap(x,8-x)
    for group in range(4):
        c.tap(9+group,8);c.led_values([(x,8-x) for x in range(1,5)],[12]*4)
    c.passed('shift-copies-notes-to-four-groups')
    c.tap(5,8)
    for x in range(1,5):c.shift_tap(x,2)
    for group in range(4):
        c.tap(9+group,8);c.led_values([(x,2) for x in range(1,5)],[12]*4)
    c.passed('shift-copies-velocities-to-four-groups')
    c.tap(3,8)
    for group in range(4):
        c.hold_tap((1,4+group),(4,4+group))
        c.playback([(1,[144,n,117]) for n in [60,62,64,65]])
        c.passed('play-step-group-'+str(group+1))

if __name__=='__main__':
    import sys
    if '--velocity' in sys.argv:run_package('A04-velocity-range-controls',velocity_ranges)
    elif '--groups' in sys.argv:run_package('A04-four-step-groups',step_groups)
    else:run_package('A04-note-range-controls',note_ranges)
