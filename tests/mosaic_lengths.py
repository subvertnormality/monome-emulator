"""Channel range gestures, wrap output and isolation through the real grid."""
from mosaic_workflows import run_package
from mosaic_channels import notes

def lengths(c):
    c.configure();c.playback(notes());c.passed('four-step-baseline')
    c.hold_tap((2,4),(3,4));c.led_values([(x,4) for x in range(1,6)],[0,15,15,0,0])
    c.playback(notes()[1:3]);c.passed('offset-two-step-loop')
    c.hold_tap((1,4),(3,4));c.led_values([(x,4) for x in range(1,6)],[15,15,15,0,0])
    c.playback(notes()[:3]);c.passed('three-step-wrap')
    # An unassigned channel has its own range; changing it must not change
    # the active channel's range or emit additional notes.
    c.tap(2,1);c.hold_tap((15,4),(2,5))
    c.led_values([(14,4),(15,4),(16,4),(1,5),(2,5),(3,5)],[0,2,2,2,2,0])
    c.playback(notes()[:3]);c.tap(1,1)
    c.led_values([(x,4) for x in range(1,6)],[15,15,15,0,0]);c.passed('independent-channel-range')
    c.hold_tap((1,4),(16,7))
    c.led_values([(1,4),(4,4),(5,4),(16,4),(1,5),(16,7)],[15,15,2,2,2,2])
    emitted=c.playback(notes(),timeout=16)
    # Four notes followed by sixty silent steps at the fixture's 90 BPM.
    gap=(emitted[4]['monotonic_ns']-emitted[3]['monotonic_ns'])/1e9
    expected=61*(60/90)/4
    assert abs(gap-expected)<=.05,dict(expected_gap_seconds=expected,actual_gap_seconds=gap)
    c.results.append(dict(kind='range-wrap',steps=64,expected_gap_seconds=expected,actual_gap_seconds=gap))
    c.passed('sixty-four-step-wrap')
    c.hold_tap((1,4),(4,4));c.playback(notes());c.passed('restore-four-step-range')

if __name__=='__main__':run_package('A05-channel-range-boundaries',lengths)
