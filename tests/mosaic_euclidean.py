"""Independent 3-in-8 rhythm table, preview, cancellation and XOR painting."""
from mosaic_workflows import run_package
from mosaic_channels import notes

def euclidean(c):
    c.configure();c.hold_tap((1,4),(8,4))
    c.tap(5,8);c.tap(5,8)
    for x,y in [(5,3),(6,2),(7,1),(8,6)]:c.tap(x,y)
    c.tap(3,8);c.tap(5,8) # trig editor
    c.playback(notes());c.passed('eight-step-loop-baseline')
    c.tap(14,2) # Euclidean
    c.tap(2,2) # broad fader minimum: one pulse
    for _ in range(2):c.tap(10,2)
    c.tap(2,3)
    for _ in range(7):c.tap(10,3)
    c.tap(16,8)
    c.led_values([(1,4),(4,4),(7,4)],[0,0,15])
    c.playback(notes());c.passed('preview-does-not-paint')
    c.tap(14,8);c.led_values([(x,4) for x in range(1,9)],[15]*4+[2]*4)
    c.playback(notes());c.passed('cancel-retains-pattern')
    c.tap(16,8);c.tap(12,8) # shift right: {2,5,8}
    c.led_values([(2,4),(5,4),(8,4)],[0,15,15]);c.tap(16,8)
    c.led_values([(x,4) for x in range(1,9)],[15,2,15,15,15,2,2,15])
    c.playback([(1,[144,n,v]) for n,v in [(60,127),(64,107),(65,97),(67,100),(62,100)]])
    c.passed('shifted-paint-xor')
    c.tap(16,8);c.led_values([(2,4),(5,4),(8,4)],[15,0,0]);c.tap(16,8)
    c.playback(notes());c.passed('repaint-restores-original')
    c.tap(16,8);c.tap(10,8) # left: back to {1,4,7}
    c.led_values([(1,4),(4,4),(7,4)],[0,0,15]);c.tap(12,8);c.tap(11,8)
    c.led_values([(1,4),(4,4),(7,4)],[0,0,15]);c.tap(16,8)
    c.playback([(1,[144,n,v]) for n,v in [(62,117),(64,107),(71,100)]])
    c.passed('left-and-center-reset')
    c.tap(16,8);c.led_values([(1,4),(4,4),(7,4)],[15,15,0]);c.tap(16,8);c.playback(notes())
    c.tap(9,2) # fill32, exceeding length8: every step selected
    c.tap(16,8);c.led_values([(1,4),(4,4),(5,4),(16,7)],[0,0,15,15]);c.tap(16,8)
    c.led_values([(x,y) for y in range(4,8) for x in range(1,17)],[2]*4+[15]*60)
    c.playback([(1,[144,n,100]) for n in [67,69,71,62]]);c.passed('dense-fill-boundary')

if __name__=='__main__':run_package('A04-euclidean-paint-controls',euclidean)
