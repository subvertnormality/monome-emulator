"""Unchanged editing/merge behavior on the isolated memory-fix candidate."""
from mosaic_candidate import prepare
from mosaic_merging import trig_modes
from mosaic_workflows import run_package

if __name__=='__main__':
    run_package('mosaic-memory-fix-regressions',trig_modes,prepare())
