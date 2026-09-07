"""Actual Mosaic MIDI routing and both documented channel mute gestures."""
import time
from mosaic_workflows import run_package

def notes(port=1,channel=1):return [(port,[143+channel,n,v]) for n,v in [(60,127),(62,117),(64,107),(65,97)]]

def silence(c):
    before=c.snapshot()['midi_count'];c.tap(1,8);c.wait_beats(2);c.tap(1,8)
    state=c.snapshot()
    emitted=[m for m in state['midi'] if m['index']>before and 144<=m['bytes'][0]<=159 and m['bytes'][2]>0]
    assert emitted==[],emitted
    assert state['midi_capture']['outstanding']==[]

def routing(c):
    c.configure();c.screen_header('Ch. 1 Device Config');c.playback(notes());c.passed('default-routing')
    c.enc(2,1);c.enc(3,1);c.key(3)
    c.playback(notes(channel=2));c.passed('midi-channel-two')
    c.enc(2,1);c.enc(3,1);c.key(3)
    c.playback(notes(port=2,channel=2));c.passed('second-midi-port')
    c.enc(3,1);c.key(2) # Cancel proposed port three.
    c.playback(notes(port=2,channel=2));c.passed('routing-cancel')
    # Cancel's native refresh returns focus to the device-map selector.
    c.enc(2,2);c.enc(3,-1);c.key(3);c.enc(2,-1);c.enc(3,-1);c.key(3)
    c.playback(notes());c.passed('routing-restored')

def muting(c):
    c.configure();c.playback(notes());c.led_values([(1,1)],[15]);c.passed('unmuted-pattern')
    c.shift_tap(1,1);c.led_values([(1,1)],[7]);silence(c);c.passed('shift-mute-silence')
    c.shift_tap(1,1);c.led_values([(1,1)],[15]);c.playback(notes());c.passed('shift-unmute-restores')
    c.action(type='grid',x=1,y=1,state=1)
    try:time.sleep(1.1)
    finally:c.action(type='grid',x=1,y=1,state=0)
    c.led_values([(1,1)],[7]);silence(c);c.passed('hold-mute-silence')
    c.action(type='grid',x=1,y=1,state=1)
    try:time.sleep(1.1)
    finally:c.action(type='grid',x=1,y=1,state=0)
    c.led_values([(1,1)],[15]);c.playback(notes());c.passed('hold-unmute-restores')
    # Muting another channel must leave channel one's output untouched.
    c.shift_tap(2,1);c.led_values([(1,1),(2,1)],[15,0]);c.playback(notes());c.passed('other-channel-isolation')

if __name__=='__main__':
    import sys
    if '--mute' in sys.argv:run_package('A05-muting-channels',muting)
    else:run_package('A05-channel-routing',routing)
