"""Independent signal-continuity and exact owned-service exit assertions."""
import math
from audio_feasibility import read_wav,metrics

def continuity(samples,rate,hz):
    # Allow only the initial 250 ms for the commanded engine transition.
    # Inspect through the last sample: stopping occurs after capture finishes.
    data=samples[int(rate*.25):]
    assert len(data)>=rate*.25,'Too little continuity evidence'
    assert all(math.isfinite(x) for x in data),'Nonfinite signal'
    peak=max(abs(x) for x in data)
    coefficient=2*math.cos(2*math.pi*hz/rate)
    residual=max(abs(data[i]-coefficient*data[i-1]+data[i-2]) for i in range(2,len(data)))
    # A sampled sine obeys this recurrence regardless of phase or host gain.
    # 1% peak + .0001 accommodates PCM quantization/resampling, not a dropout.
    limit=peak*.01+.0001
    assert residual<limit,dict(continuity_residual=residual,limit=limit)
    return dict(max_residual=residual,limit=limit,excluded_initial_seconds=.25,excluded_tail_seconds=0)

def signal(path,hz,minimum_rms=.03):
    rate,channels=read_wav(path);assert len(channels)==2,'Stereo capture required'
    result=[]
    for channel in channels:
        row=metrics(channel,rate,hz)
        assert minimum_rms<row['rms']<.3 and row['tone_energy_fraction']>.85,row
        row['continuity']=continuity(channel,rate,hz);result.append(row)
    return result

def exits(rows,desktop_exit):
    expected={'desktop-audio','matron','sclang','crone','jack'}
    assert len(rows)==len(expected) and {r['service'] for r in rows}==expected,rows
    for row in rows:
        allowed=(desktop_exit,) if row['service']=='desktop-audio' else ((0,-15) if row['service']=='sclang' else (0,))
        assert row['returncode'] in allowed,row
