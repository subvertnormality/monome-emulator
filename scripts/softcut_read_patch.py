"""Explicit-duration reads must obey both soundfile and registered-buffer bounds."""
import difflib

def apply(source):
    path=source/'crone/src/BufDiskWorker.cpp';before=path.read_text()
    marker='        frDur = secToFrame(dur);\n    }\n\n    auto numSrcChan = file.channels();'
    if before.count(marker)!=2:raise ValueError('Expected mono/stereo read bounds sites changed')
    after=before.replace(marker,'        frDur = secToFrame(dur);\n'
        '        // Explicit lengths obey the same source/destination bounds as read-to-end.\n'
        '        clamp(frDur, static_cast<size_t>(file.frames()) - frSrc);\n'
        '        clamp(frDur, bufFrames - frDst);\n    }\n\n    auto numSrcChan = file.channels();')
    path.write_text(after)
    return ''.join(difflib.unified_diff(before.splitlines(True),after.splitlines(True),
        fromfile='a/crone/src/BufDiskWorker.cpp',tofile='b/crone/src/BufDiskWorker.cpp'))
