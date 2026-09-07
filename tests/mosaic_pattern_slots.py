"""All sixteen pattern slots, assignments, and alternate editor selection gestures."""
from mosaic_workflows import run_package
from mosaic_channels import notes
from mosaic_editor_ranges import hold

PITCHES=[60,62,64,65,67,69,71]

def expected(slot):
    if slot==1:return notes()
    offset=(slot-2)%7
    return [(1,[144,PITCHES[offset],100]),(1,[144,PITCHES[(offset+1)%7],100])]

def slots(c):
    c.configure();c.playback(expected(1));c.passed('slot-1-baseline')
    for slot in range(2,17):
        c.tap(5,8);c.tap(slot,1)
        c.led_values([(x,4) for x in range(1,5)],[2]*4)
        c.tap(1,4);c.tap(2,4);c.tap(5,8)
        offset=(slot-2)%7
        c.tap(1,7-offset);c.tap(2,7-(offset+1)%7)
        c.tap(3,8);c.tap(slot-1,2);c.tap(slot,2)
        c.led_values([(slot-1,2),(slot,2)],[2,15])
        c.playback(expected(slot));c.passed('slot-'+str(slot)+'-independent-edit')
    # Revisiting the first slot must retain the original four-note pattern.
    c.tap(16,2);c.tap(1,2);c.playback(expected(1));c.passed('first-slot-preserved')
    c.tap(5,8);c.tap(5,8) # Note editor, still editing slot16.
    c.shift_tap(1,1);c.tap(4,3) # Select pattern1, change F4 to G4.
    c.playback(notes()[:3]+[(1,[144,67,97])]);c.passed('note-shift-selects-pattern')
    hold(c,16,1);c.tap(1,3) # Select last slot and change its first note to G4.
    c.tap(3,8);c.tap(1,2);c.tap(16,2)
    c.playback([(1,[144,67,100]),expected(16)[1]]);c.passed('note-hold-selects-pattern')
    c.tap(5,8);c.tap(5,8);c.tap(5,8) # Velocity editor.
    c.shift_tap(1,1);c.tap(4,2)
    c.tap(3,8);c.tap(16,2);c.tap(1,2)
    c.playback(notes()[:3]+[(1,[144,67,117])]);c.passed('velocity-shift-selects-pattern')
    c.tap(5,8);c.tap(5,8);c.tap(5,8)
    hold(c,16,1);c.tap(2,3)
    c.tap(3,8);c.tap(1,2);c.tap(16,2)
    c.playback([(1,[144,67,100]),(1,[144,expected(16)[1][1][1],107])])
    c.passed('velocity-hold-selects-pattern')
    c.screen_header('Ch. 1 Device Config');c.passed('script-page-retained')

if __name__=='__main__':run_package('A04-sixteen-pattern-slots',slots)
