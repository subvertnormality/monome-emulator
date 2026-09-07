"""Complete root, degree and rotation selectors with independent pitch arithmetic."""
from mosaic_workflows import run_package
from mosaic_scales import setup,play

MAJOR=[0,2,4,5,7,9,11]

def roots(c):
    setup(c);c.enc(2,-1)
    for root in range(12):
        if root:c.enc(3,1);c.key(3)
        play(c,[60+root+n for n in MAJOR]);c.passed('root-'+str(root))
    c.enc(3,1);c.key(3);play(c,[71+n for n in MAJOR]);c.passed('root-upper-clamp')
    c.enc(3,-12);c.key(3);play(c,[60+n for n in MAJOR]);c.passed('root-lower-clamp')

def degree_pitches(degree):
    return [60+MAJOR[(degree+i)%7]+12*((degree+i)//7) for i in range(7)]

def degrees(c):
    setup(c);c.enc(2,1)
    for degree in range(7):
        if degree:c.enc(3,1);c.key(3)
        play(c,degree_pitches(degree));c.passed('degree-'+str(degree+1))
    c.enc(3,1);c.key(3);play(c,degree_pitches(6));c.passed('degree-upper-clamp')
    c.enc(3,-7);c.key(3);play(c,degree_pitches(0));c.passed('degree-lower-clamp')

def rotation_pitches(rotation):
    # Invert by lowering the highest N positions of this seven-note voicing.
    return [60+n-(12 if i>=7-rotation else 0) for i,n in enumerate(MAJOR)]

def rotations(c):
    setup(c);c.enc(2,3)
    for rotation in range(7):
        if rotation:c.enc(3,1);c.key(3)
        play(c,rotation_pitches(rotation));c.passed('rotation-'+str(rotation))
    c.enc(3,1);c.key(3);play(c,rotation_pitches(6));c.passed('rotation-upper-clamp')
    c.enc(3,-7);c.key(3);play(c,rotation_pitches(0));c.passed('rotation-lower-clamp')

if __name__=='__main__':
    import sys
    if '--degrees' in sys.argv:run_package('A06-seven-scale-degrees',degrees)
    elif '--rotations' in sys.argv:run_package('A06-seven-scale-rotations',rotations)
    else:run_package('A06-twelve-scale-roots',roots)
