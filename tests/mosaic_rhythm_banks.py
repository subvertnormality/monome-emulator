"""Classic drum banks and numeric masks, with literal rhythm data oracles."""
from mosaic_workflows import run_package
from mosaic_channels import silence
from automation.protocol import ROOT,read_json

def banks(c):
    oracle=read_json(ROOT/'fixtures/oracles/rhythm-banks.json')
    c.configure();c.hold_tap((1,4),(16,4))
    c.tap(5,8)
    for x in range(1,5):c.tap(x,4) # empty pattern, retain routing
    c.tap(5,8)
    for x in range(1,17):c.tap(x,7-((x-1)%7))
    c.tap(3,8);c.tap(5,8)
    cells=[(x,y) for y in range(4,8) for x in range(1,17)]
    c.led_values(cells,[2]*64);silence(c);c.passed('empty-pattern')
    def paint(steps):
        c.tap(16,8)
        # Nonempty previews flash coherently. Empty banks have no step flashes.
        if steps:c.led_values([((steps[0]-1)%16+1,4)],[15])
        else:c.led_values([(14,8)],[15])
        c.tap(16,8)
        c.led_values(cells,[15 if i%16+1 in steps else 2 for i in range(64)])
        if steps:
            pitches=[60,62,64,65,67,69,71]
            velocities=[127,117,107,97]+[100]*12
            c.playback([(1,[144,pitches[(s-1)%7],velocities[s-1]]) for s in steps],timeout=6)
        else:silence(c)
        c.tap(16,8)
        if steps:c.led_values([((steps[0]-1)%16+1,4)],[0])
        else:c.led_values([(14,8)],[15])
        c.tap(16,8);c.led_values(cells,[2]*64)
    c.tap(12,2);c.tap(2,2);c.tap(10,2) # drum pattern2
    for bank in range(1,6):
        c.tap(11+bank,3);paint(oracle['drum_pattern_2'][str(bank)]);c.passed('drum-bank-'+str(bank))
    c.tap(15,2);c.tap(2,2);c.tap(2,3) # numeric prime1, factor1
    for bank in range(1,5):
        c.tap(11+bank,3);paint(oracle['numeric_prime_1_factor_1'][str(bank)]);c.passed('numeric-mask-'+str(bank))

if __name__=='__main__':run_package('A04-rhythm-bank-controls',banks)
