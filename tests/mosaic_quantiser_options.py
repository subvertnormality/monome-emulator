"""Global quantiser options via native norns parameter-menu controls."""
from mosaic_workflows import run_package
from mosaic_global_masks import held_delta


def option(c,position,delta):
    previous=getattr(c,'quantiser_menu_position',None)
    if previous is None:c.parameter_menu();previous=0
    else:c.key(1)
    c.enc(2,position-previous);c.enc(3,delta);c.key(1)
    c.quantiser_menu_position=position


def play(c,pitches):
    c.playback([(1,[144,n,v]) for n,v in zip(pitches,[127,117,107,97])])


def pentatonic(c):
    c.configure();c.tap(5,8);c.tap(5,8);c.tap(3,4);c.tap(4,1);c.tap(3,8)
    play(c,[60,62,65,71]);c.passed('diatonic-baseline')
    option(c,19,1);play(c,[60,62,64,72]);c.passed('all-pentatonic-enabled')
    option(c,19,-1);play(c,[60,62,65,71]);c.passed('all-pentatonic-disabled')
    c.screen_header('Ch. 1 Device Config');c.passed('script-view-restored')


def masks(c):
    c.configure();c.enc(1,-4);held_delta(c,1,72)
    play(c,[71,62,64,65]);c.passed('default-snap-mask')
    c.tap(4,8);c.enc(2,1);c.enc(3,1);c.key(3)
    c.enc(2,2);c.enc(3,1);c.key(3);c.tap(3,8)
    play(c,[71,64,65,67]);c.passed('snap-ignores-degree-rotation')
    option(c,16,-1);held_delta(c,1,-1)
    play(c,[70,64,65,67]);c.passed('snap-disabled-chromatic-mask')
    option(c,17,1)
    play(c,[71,64,65,67]);c.passed('full-quantise-overrides-snap-off')
    held_delta(c,1,1)
    play(c,[60,64,65,67]);c.passed('full-quantise-degree-and-rotation')
    option(c,17,-1)
    play(c,[71,64,65,67]);c.passed('full-quantise-disabled')
    option(c,16,1);held_delta(c,1,-1)
    play(c,[69,64,65,67]);c.passed('snap-restored')
    c.screen_header('Ch. 1 Note Masks');c.passed('script-view-restored')

if __name__=='__main__':
    import sys
    if '--masks' in sys.argv:run_package('A06-mask-quantiser-options',masks)
    else:run_package('A06-all-pentatonic-option',pentatonic)
