"""Four additional chord voices, step isolation, bounds and removal."""
import time
from mosaic_workflows import run_package
from mosaic_channels import notes
from mosaic_masks import clear_step

def chord(c,amount):
    c.action(type='grid',x=1,y=4,state=1)
    try:time.sleep(.05);c.enc(3,amount)
    finally:c.action(type='grid',x=1,y=4,state=0)
    time.sleep(.1)

def chords(c):
    c.configure();c.enc(1,-4);c.screen_header('Ch. 1 Note Masks');c.enc(2,3)
    def play(pitches):
        c.playback([(1,[144,n,127]) for n in pitches]+notes()[1:])
    chord(c,2);play([60,64]);c.passed('third-above-root')
    c.enc(2,1);chord(c,4);play([60,64,67]);c.passed('triad')
    c.enc(2,1);chord(c,7);play([60,64,67,72]);c.passed('octave-voice')
    c.enc(2,1);chord(c,9);play([60,64,67,72,76]);c.passed('all-four-additional-voices')
    chord(c,5);play([60,64,67,72,84]);c.passed('upper-fourth-voice-bound')
    chord(c,1);play([60,64,67,72,84]);c.passed('upper-bound-clamps')
    chord(c,-28);play([60,64,67,72,36]);c.passed('lower-fourth-voice-bound')
    chord(c,-1);play([60,64,67,72,36]);c.passed('lower-bound-clamps')
    clear_step(c,1);c.playback(notes());c.passed('clear-all-step-voices')

if __name__=='__main__':run_package('A06-adding-chords',chords)
