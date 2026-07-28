#!/usr/bin/env python3
"""Demo: HyperSynth's chord matrix + mid-phrase chord-shape switching.

HyperSynth (instrument type 5) has a 16-slot chord matrix beyond the
standard instrument parameters: each slot is a bitmask of which of its 6
oscillators are active plus a semitone offset per oscillator. Playing a
note plays the root + every active oscillator's offset simultaneously —
one instrument, one note, several pitches at once.

The CRD FX command (M8HypersynthFX.CRD) selects which of the 16 chord
slots is active, and it can be set per phrase step — so a single held
note can cycle through entirely different chord voicings across
successive steps. This demo defines eight common chord shapes in the
matrix and plays through all of them at a fixed root note to show the
whole palette clearly, then closes with a short progression that also
varies the root, combining note changes with chord-shape switching.

Output: tmp/demos/hypersynth_chords/HYPERSYNTH-CHORDS.m8s
"""
from pathlib import Path

from m8.api.chain import M8ChainStep
from m8.api.fx import M8FXTuple, M8HypersynthFX
from m8.api.instruments.hypersynth import M8Chord, M8HyperSynth, M8HyperSynthModDest
from m8.api.modulator import M8ADSRModulator
from m8.api.phrase import M8Note, M8Phrase, M8PhraseStep
from m8.api.project import M8Project


PROJECT_NAME = "HYPERSYNTH-CHORDS"
OUTPUT_DIR = Path("tmp/demos/hypersynth_chords")
BPM = 96

# Chord shapes as (name, mask, offsets) — mask bit i enables oscillator i;
# offsets[i] is that oscillator's semitone offset from the root (only
# meaningful where the mask enables it).
CHORD_SHAPES = [
    ("Major",     0x07, [0, 4, 7, 0, 0, 0]),
    ("Minor",     0x07, [0, 3, 7, 0, 0, 0]),
    ("Sus4",      0x07, [0, 5, 7, 0, 0, 0]),
    ("Major 7th", 0x0F, [0, 4, 7, 11, 0, 0]),
    ("Minor 7th", 0x0F, [0, 3, 7, 10, 0, 0]),
    ("Dom 7th",   0x0F, [0, 4, 7, 10, 0, 0]),
    ("Power 5th", 0x03, [0, 7, 0, 0, 0, 0]),
    ("Add9",      0x0F, [0, 4, 7, 14, 0, 0]),
]


def build_instrument():
    """HyperSynth with a slow pad-like envelope — chords read best sustained,
    not plucked."""
    inst = M8HyperSynth(name="CHORDS")
    inst.filter_type = 1  # lowpass
    inst.cutoff = 0xB0
    inst.resonance = 0x40
    inst.amp = 0xC0
    inst.pan = 0x80
    inst.dry = 0xC0
    inst.reverb_send = 0x60

    inst.modulators[0] = M8ADSRModulator(
        destination=M8HyperSynthModDest.VOLUME,
        attack=0x20, decay=0x40, sustain=0xC0, release=0x60,
    )

    for slot, (_, mask, offsets) in enumerate(CHORD_SHAPES):
        inst.chords[slot] = M8Chord(mask=mask, offsets=offsets)

    return inst


def build_palette_phrase():
    """Steps 0-14 (every other step): hold C_4, cycle CRD through all
    eight defined chord shapes in order — the full palette, one instrument,
    one note, eight different voicings."""
    phrase = M8Phrase()
    for i, (name, _, _) in enumerate(CHORD_SHAPES):
        step_index = i * 2
        step = M8PhraseStep(note=M8Note.C_4, velocity=0x7F, instrument=0)
        step.fx[0] = M8FXTuple(key=M8HypersynthFX.CRD, value=i)
        phrase[step_index] = step
    return phrase


def build_progression_phrase():
    """A short progression that varies both root note and chord shape —
    I (C major) - vi (A minor) - IV (F major, sus4 passing chord) - V (G dominant 7th)."""
    phrase = M8Phrase()
    progression = [
        (0, M8Note.C_4, 0),   # C major
        (4, M8Note.A_3, 1),   # A minor
        (8, M8Note.F_3, 2),   # F sus4 (passing)
        (10, M8Note.F_3, 0),  # F major
        (12, M8Note.G_3, 5),  # G dominant 7th
    ]
    for step_index, note, chord_slot in progression:
        step = M8PhraseStep(note=note, velocity=0x70, instrument=0)
        step.fx[0] = M8FXTuple(key=M8HypersynthFX.CRD, value=chord_slot)
        phrase[step_index] = step
    return phrase


def main():
    project = M8Project.initialise()
    project.metadata.name = PROJECT_NAME
    project.metadata.tempo = BPM

    project.instruments[0] = build_instrument()

    print("Chord matrix:")
    for slot, (name, mask, offsets) in enumerate(CHORD_SHAPES):
        print(f"  slot {slot}: {name:<10} mask=0x{mask:02X} offsets={offsets}")

    project.phrases[0] = build_palette_phrase()
    project.phrases[1] = build_progression_phrase()

    project.chains[0][0] = M8ChainStep(phrase=0, transpose=0)
    project.chains[0][1] = M8ChainStep(phrase=1, transpose=0)

    for row in range(4):
        project.song[row][0] = 0

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUTPUT_DIR / f"{PROJECT_NAME}.m8s"
    project.write_to_file(str(out_path))

    print(f"\n✓ Wrote {out_path}")
    print("  phrase 0: palette walk — one held note, all 8 chord shapes")
    print("  phrase 1: I-vi-IV-V progression combining root + chord changes")
    print("  ship to your M8 with: python tools/sync.py push")


if __name__ == "__main__":
    main()
