"""Hand-authored pitch tables applied through native scale/root/degree controls."""
from mosaic_workflows import run_package
from automation.protocol import ROOT,read_json

def harmony(c):
    oracle=read_json(ROOT/'fixtures/oracles/harmony.json')
    def play(name):c.playback([(1,[144,n,v]) for n,v in zip(oracle['pitches'][name],oracle['velocities'])])
    c.configure();c.tap(5,8);c.tap(5,8);c.tap(4,1) # Seventh degree makes rotation observable.
    c.wait(lambda s:s['grid'][3]==12);play('c_major');c.passed('major-diatonic-degrees')
    c.tap(4,8);c.screen_header('Scale slot 1 ',selected=1,tabs=3);c.led_values([(1,3)],[15])
    c.enc(3,2);c.key(3) # Major -> harmonic major -> minor
    c.enc(2,-1);c.enc(3,4);c.key(3) # Root C -> E
    play('e_minor');c.passed('root-and-minor-scale')
    c.enc(2,2);c.enc(3,1);c.key(3);play('e_minor_degree_two');c.passed('second-scale-degree')
    c.enc(2,2);c.enc(3,1);c.key(3);play('e_minor_degree_two_rotation_one');c.passed('rotation-lowers-seventh')
    c.enc(2,-1);c.enc(3,12);c.key(3);play('transpose_plus_twelve');c.passed('transpose-plus-twelve')
    c.enc(3,1);c.key(3);play('transpose_plus_twelve');c.passed('upper-transpose-bound')
    c.enc(3,-24);c.key(3);play('transpose_minus_twelve');c.passed('transpose-minus-twelve')
    c.enc(3,-1);c.key(3);play('transpose_minus_twelve');c.passed('lower-transpose-bound')
    c.enc(3,1);c.key(2);play('transpose_minus_twelve');c.passed('cancel-scale-change')
    c.enc(3,12);c.key(3) # transposition zero
    c.enc(2,1);c.enc(3,-1);c.key(3) # rotation zero
    c.enc(2,-2);c.enc(3,-1);c.key(3) # degree I
    c.enc(2,-2);c.enc(3,-4);c.key(3) # root C
    c.enc(2,1);c.enc(3,-2);c.key(3) # major
    play('c_major');c.screen_header('Scale slot 1 ',selected=1,tabs=3);c.passed('restore-major-harmony')

if __name__=='__main__':run_package('A06-harmony-design',harmony)
