"""Literal 3/3/2 segment expectations across all eight tresillo multipliers."""
from mosaic_workflows import run_package

# Bank1 pattern2 is a 24-bit input with hits3/16. Form A(3m), A(3m), B(2m).
# These hand-derived positions do not call the application algorithm.
TRES={8:[3,6],16:[3,9,15],24:[3,12,21],32:[3,15,27],
      40:[3,18,33],48:[3,16,21,34,39],56:[3,16,24,37,45],
      64:[3,16,27,40,51,64]}

def setup(c):
    c.configure();c.tap(5,8)
    for x in range(1,5):c.tap(x,4)
    c.tap(5,8)
    for x in range(1,17):c.shift_tap(x,7-((x-1)%6))
    c.tap(3,8);c.tap(5,8);c.tap(13,2);c.tap(12,3)
    c.tap(2,2);c.tap(10,2);c.tap(2,3);c.tap(10,3)
    c.enc(1,1);c.enc(3,-8)
    c.screen_header('Trig editor options',selected=2,tabs=2)

def rhythm(c,length,steps):
    c.tap(3,8);c.hold_tap((1,4),((length-1)%16+1,4+(length-1)//16));c.tap(5,8)
    c.tap(16,8)
    first=((steps[0]-1)%16+1,4+(steps[0]-1)//16)
    c.led_values([first],[15]);c.tap(16,8)
    cells=[(x,y) for y in range(4,8) for x in range(1,17)]
    c.led_values(cells,[15 if i%length+1 in steps else 2 for i in range(64)])
    pitches=[60,62,64,65,67,69]
    velocities=[127,117,107,97]+[100]*60
    expected=[(1,[144,pitches[((s-1)%16)%6],velocities[s-1]]) for s in steps]
    c.playback(expected,timeout=length/3+3)
    c.tap(16,8);c.led_values([first],[0]);c.tap(16,8);c.led_values(cells,[2]*64)

def tresillo(c):
    setup(c);c.passed('tresillo-input-setup')
    for i,(length,steps) in enumerate(TRES.items()):
        if i:c.enc(3,1)
        rhythm(c,length,steps);c.passed('multiplier-'+str(length))

def drum_boundary(c):
    setup(c);c.tap(13,3);c.enc(3,7)
    rhythm(c,64,list(range(1,65,8)));c.passed('drum-bank-64-step-tresillo')

if __name__=='__main__':
    import sys
    if '--candidate' in sys.argv:
        from mosaic_candidate import prepare
        from automation.protocol import ROOT
        run_package('A04-tresillo-drum-boundary-candidate',drum_boundary,prepare(ROOT/'fixtures/apps/mosaic-patches/tresillo.json'))
    elif '--drum-boundary' in sys.argv:run_package('A04-tresillo-drum-boundary-baseline',drum_boundary)
    else:run_package('A04-tresillo-multipliers',tresillo)
