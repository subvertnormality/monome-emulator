"""Optional buffer capacity for a 2048-frame desktop JACK period."""
import difflib

def apply(source):
    patch=''
    for name,symbol in [('MixerClient.h','MaxBufFrames'),('SoftcutClient.h','MaxBlockFrames')]:
        path=source/'crone/src'/name
        before=path.read_text();old='enum { '+symbol+' = 2048 };'
        if before.count(old)!=1:raise ValueError('Pinned crone buffer capacity changed; inspect upstream')
        after=before.replace(old,'enum { '+symbol+' = 4096 };')
        path.write_text(after)
        patch+=''.join(difflib.unified_diff(before.splitlines(True),after.splitlines(True),
            fromfile='a/crone/src/'+name,tofile='b/crone/src/'+name))
    return patch
