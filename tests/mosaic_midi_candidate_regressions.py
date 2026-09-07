"""Unchanged chord workflow on the MIDI/mask compatibility candidate."""
from mosaic_candidate import prepare
from mosaic_chords import chords
from mosaic_workflows import run_package
from automation.protocol import ROOT

if __name__=='__main__':
    run_package('mosaic-midi-fix-chord-regressions',chords,prepare(ROOT/'fixtures/apps/mosaic-patches/midi-counts.json'))
