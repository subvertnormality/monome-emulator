"""Optional startup-chime control; default preserves official norns behavior."""
import difflib

def apply(source):
    path=source/'sc/core/Crone.sc';before=path.read_text()
    old='\t\t{ SinOsc.ar([218,223]) * 0.125 * EnvGen.ar(Env.linen(2, 4, 6), doneAction:2) }.play(server);'
    if before.count(old)!=1:raise ValueError('Pinned startup chime changed; inspect upstream before applying')
    new='\t\tif ("NORNS_EMU_STARTUP_CHIME".getenv != "0") {\n\t'+old+'\n\t\t};'
    after=before.replace(old,new);path.write_text(after)
    return ''.join(difflib.unified_diff(before.splitlines(True),after.splitlines(True),
        fromfile='a/sc/core/Crone.sc',tofile='b/sc/core/Crone.sc'))
