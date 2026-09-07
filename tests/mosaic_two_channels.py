"""One external pattern on two MIDI channels with independent loop lengths."""
import math
from mosaic_workflows import run_package
from mosaic_channels import notes

def paired(first_length):
    result=[]
    for step in range(first_length*3//math.gcd(first_length,3)):
        first=notes()[step%first_length]
        second=notes(channel=2)[step%3]
        # Pinned m_clock.lua registers channel clocks from 17 down to 1.
        # Preserve that emission order; never sort captured MIDI to match.
        result.extend([(second[0],[second[1][0],second[1][1]+12,second[1][2]]),first])
    return result

def channels(c):
    c.configure();c.tap(2,1);c.enc(3,1);c.key(3)
    c.enc(2,1);c.enc(3,-15);c.enc(3,1);c.key(3) # explicitly select MIDI channel2
    c.tap(1,2);c.tap(11,8);c.hold_tap((1,4),(3,4))
    c.led_values([(x,4) for x in range(1,5)],[15,15,15,0])
    c.playback(paired(4),cycles=1);c.passed('shared-pattern-independent-loops')
    c.shift_tap(2,1);c.playback(notes());c.passed('mute-second-preserves-first')
    c.shift_tap(2,1);c.playback(paired(4),cycles=1);c.passed('unmute-restores-paired-output')
    c.tap(1,2);c.playback(notes());c.passed('unassign-second-preserves-first')
    c.tap(1,2);c.playback(paired(4),cycles=1);c.passed('reassign-restores-second')
    c.tap(1,1);c.hold_tap((1,4),(2,4))
    c.led_values([(x,4) for x in range(1,5)],[15,15,0,0])
    c.playback(paired(2),cycles=2);c.passed('change-first-loop-independently')
    c.tap(2,1);c.led_values([(x,4) for x in range(1,5)],[15,15,15,0])
    c.tap(1,1);c.hold_tap((1,4),(4,4));c.playback(paired(4),cycles=1)
    c.screen_header('Ch. 1 Device Config');c.passed('restore-original-loop-pair')

if __name__=='__main__':run_package('A05-two-active-channels',channels)
