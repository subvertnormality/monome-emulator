"""Pattern length gestures verified against real note-off timestamps."""
from mosaic_workflows import run_package
from mosaic_editor_ranges import hold

def play(c,pitches,durations):
    emitted=c.playback([(1,[144,n,v]) for n,v in pitches],cycles=3,timeout=5)
    state=c.snapshot();rows=[]
    for note,length in zip(emitted,durations):
        off=next(m for m in state['midi'] if m['index']>note['index'] and
                 m['port']==1 and m['bytes']==[128,note['bytes'][1],note['bytes'][2]])
        actual=(off['monotonic_ns']-note['monotonic_ns'])/1e9
        rows.append(dict(pitch=note['bytes'][1],steps=length,expected_seconds=length/6,
                         actual_seconds=actual,error_ms=1000*(actual-length/6)))
    c.results.append(dict(kind='note-durations',rows=rows))
    assert all(abs(row['error_ms'])<=10 for row in rows),rows

def setup(c):
    c.configure();c.hold_tap((1,4),(8,4));c.tap(5,8)
    for x in (2,3,4):c.tap(x,4)
    c.tap(5,4);c.tap(5,8);c.tap(5,3);c.tap(3,8);c.tap(5,8)

def lengths(c):
    setup(c);pair=[(60,127),(67,100)]
    play(c,pair,[1,1]);c.passed('single-step-note-durations')
    c.hold_tap((1,4),(3,4));c.led_values([(x,4) for x in range(1,6)],[15,5,5,2,15])
    play(c,pair,[3,1]);c.passed('extend-note-through-held-range')
    hold(c,1,4);c.led_values([(x,4) for x in range(1,6)],[15,2,2,2,15])
    play(c,pair,[1,1]);c.passed('long-press-restores-one-step')
    c.hold_tap((2,4),(4,4));c.led_values([(x,4) for x in range(1,6)],[15,2,2,2,15])
    play(c,pair,[1,1]);c.passed('empty-step-cannot-acquire-length')

def collision(c):
    setup(c);c.hold_tap((1,4),(4,4));c.tap(3,4)
    c.led_values([(x,4) for x in range(1,6)],[15,5,15,2,15])
    # README Adding Trigs: one trig's duration ends upon meeting another.
    play(c,[(60,127),(64,107),(67,100)],[2,1,1])
    c.passed('next-trig-ends-preceding-note')

if __name__=='__main__':
    import sys
    if '--candidate' in sys.argv:
        from mosaic_candidate import prepare
        from automation.protocol import ROOT
        code=prepare(ROOT/'fixtures/apps/mosaic-patches/pattern-lengths.json')
        run_package('A04-pattern-length-cutoff-candidate',collision,code)
        run_package('A04-pattern-length-cutoff-regressions',lengths,code)
    elif '--collision-baseline' in sys.argv:run_package('A04-pattern-length-collision-baseline',collision)
    else:run_package('A04-pattern-length-controls',lengths)
