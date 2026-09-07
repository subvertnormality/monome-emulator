"""Independent set-membership and literal musical oracles for real merge controls."""
from mosaic_workflows import run_package

def setup_patterns(c):
    c.configure();c.tap(5,8)
    c.tap(3,4);c.tap(4,4) # A={1,2}
    c.tap(5,8);c.tap(2,5) # A notes C4,E4; velocities 127,117
    c.tap(5,8);c.tap(5,8)
    c.tap(2,1);c.tap(2,4);c.tap(3,4) # B={2,3}
    c.tap(5,8);c.tap(2,5);c.tap(3,3) # B notes E4,G4
    c.tap(5,8);c.tap(2,4);c.tap(3,4) # B velocities 97,97
    c.tap(3,8);c.tap(2,2) # assign B as well as A
    c.screen_header('Ch. 1 Device Config')
    c.led_values([(1,2),(2,2)],[15,15]);c.passed('two-pattern-assignment')

def trig_modes(c):
    setup_patterns(c)
    cells=[(x,4) for x in range(1,5)]
    c.led_values(cells,[15,2,15,2])
    c.playback([(1,[144,60,127]),(1,[144,67,97])]);c.passed('skip-exclusive-steps')
    c.tap(14,8);c.led_values(cells,[2,15,2,2])
    c.playback([(1,[144,64,107])]);c.passed('only-intersection')
    c.tap(14,8);c.led_values(cells,[15,15,15,2])
    c.playback([(1,[144,60,127]),(1,[144,64,107]),(1,[144,67,97])]);c.passed('all-union')
    c.tap(14,8);c.led_values(cells,[15,2,15,2])
    c.playback([(1,[144,60,127]),(1,[144,67,97])]);c.passed('mode-cycle-restores-skip')
    c.tap(1,2);c.tap(2,2);c.led_values(cells,[2,2,2,2])
    before=c.snapshot()['midi_count'];c.tap(1,8);c.wait_beats(2);c.tap(1,8)
    after=[m for m in c.snapshot()['midi'] if m['index']>before and 144<=m['bytes'][0]<=159 and m['bytes'][2]>0]
    assert after==[],after;c.passed('empty-assignment-silence')

def lower_documented_baseline(c):
    setup_patterns(c)
    c.tap(14,8);c.tap(14,8) # All: expose the overlapping step
    c.tap(16,8);c.tap(16,8) # Average -> Higher -> Lower velocity
    c.led_values([(16,8)],[8])
    # README: average(117,97)-min(117,97) = 107-97 = 10.
    # Keep this baseline expectation independent from pattern.lua's formula.
    c.playback([(1,[144,60,127]),(1,[144,64,10]),(1,[144,67,97])])
    c.passed('lower-matches-documented-formula')

if __name__=='__main__':
    import sys
    if '--lower-baseline' in sys.argv:run_package('A05-lower-doc-baseline',lower_documented_baseline)
    else:run_package('A05-trig-merge-modes',trig_modes)
