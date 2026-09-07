"""Exercise all ten scale choices using complete seven-degree pitch tables."""
from mosaic_workflows import run_package
from automation.protocol import ROOT,read_json

def setup(c):
    c.configure();c.hold_tap((1,4),(7,4));c.tap(5,8)
    for x in range(5,8):c.tap(x,4)
    c.tap(5,8)
    for x in range(1,8):c.tap(x,8-x)
    c.tap(4,8);c.screen_header('Scale slot 1 ',selected=1,tabs=3)

def play(c,pitches):
    c.playback([(1,[144,n,v]) for n,v in zip(pitches,[127,117,107,97,100,100,100])])

def scales(c):
    setup(c);tables=read_json(ROOT/'fixtures/oracles/scales.json')['scales']
    for i,scale in enumerate(tables):
        if i:c.enc(3,1);c.key(3)
        play(c,[60+n for n in scale['intervals']]);c.passed(scale['name'])
    c.enc(3,1);c.key(3);play(c,[60+n for n in tables[-1]['intervals']]);c.passed('upper-scale-clamp')
    c.enc(3,-10);c.key(3);play(c,[60+n for n in tables[0]['intervals']]);c.passed('lower-scale-clamp')

if __name__=='__main__':run_package('A06-ten-scale-choices',scales)
