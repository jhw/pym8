#!/usr/bin/env python

"""
Wavsynth 303 Demo - Acid bassline-style demo using M8 Wavsynth

Creates an M8 project with:
- 16 wavsynth instruments (0x00-0x0F), each with a different wave shape
- Each instrument has two ADSR modulators (volume and cutoff)
- 16 phrases (0x00-0x0F), each with different random note patterns
- 16 chains (0x00-0x0F), each referencing the corresponding phrase
- Song arrangement: all 16 chains stacked vertically in track 0

Output: tmp/demos/wavsynth_303/WAVSYNTH-303.m8s
"""

import random
from pathlib import Path

from m8.api.project import M8Project
from m8.api.instruments.wavsynth import M8Wavsynth, M8WavsynthParam, M8WavShape, M8WavsynthModDest
from m8.api.instrument import M8FilterType, M8LimiterType
from m8.api.phrase import M8Phrase, M8PhraseStep, M8Note
from m8.api.chain import M8Chain, M8ChainStep
from m8.api.fx import M8FXTuple, M8SequenceFX

# Configuration
PROJECT_NAME = "WAVSYNTH-303"
OUTPUT_DIR = Path("tmp/demos/wavsynth_303")
BPM = 135
SEED = 42

# Note choices for random bass pattern (C and D# at octaves 3 and 4, plus C5)
BASS_NOTES = [M8Note.C_3, M8Note.DS_3, M8Note.C_4, M8Note.DS_4, M8Note.C_5]

# Wave shapes for each of the 16 instruments
WAVE_SHAPES = [
    M8WavShape.PULSE12,      # 0x00
    M8WavShape.PULSE25,      # 0x01
    M8WavShape.PULSE50,      # 0x02
    M8WavShape.PULSE75,      # 0x03
    M8WavShape.SAW,          # 0x04
    M8WavShape.TRIANGLE,     # 0x05
    M8WavShape.SINE,         # 0x06
    M8WavShape.NOISE_PITCHED,# 0x07
    M8WavShape.WT_CRUSH,     # 0x08
    M8WavShape.WT_FOLDING,   # 0x09
    M8WavShape.WT_FUZZY,     # 0x0A
    M8WavShape.WT_LIQUID,    # 0x0B
    M8WavShape.WT_MORPHING,  # 0x0C
    M8WavShape.WT_MYSTIC,    # 0x0D
    M8WavShape.WT_TIDAL,     # 0x0E
    M8WavShape.WT_WAVES,     # 0x0F
]


def create_wavsynth_303_project():
    """Create the Wavsynth 303 M8 project with 16 variations."""
    print(f"Creating Wavsynth 303 demo: {PROJECT_NAME}")
    print(f"BPM: {BPM}, Seed: {SEED}")
    print(f"Creating 16 instruments, phrases, and chains (0x00-0x0F)")

    # Initialize RNG with seed for reproducible results
    rng = random.Random(SEED)

    # Initialize project
    project = M8Project.initialise()
    project.metadata.name = PROJECT_NAME
    project.metadata.tempo = BPM
    project.metadata.directory = "/Songs/pym8-demos/wavsynth-303/"

    # Create 16 variations (0x00-0x0F)
    for idx in range(16):
        print(f"\n[{idx:02X}] Creating variation {idx + 1}/16")

        # Create wavsynth instrument with unique wave shape
        wave_shape = WAVE_SHAPES[idx]
        wave_name = wave_shape.name
        wavsynth = M8Wavsynth(name=f"AC-{wave_name[:8]}")  # Truncate to fit M8 name limit

        # Set synth parameters
        wavsynth.set(M8WavsynthParam.SHAPE, wave_shape)
        wavsynth.set(M8WavsynthParam.FILTER_TYPE, M8FilterType.LOWPASS)  # Low pass filter
        wavsynth.set(M8WavsynthParam.CUTOFF, 0x20)       # Low cutoff for filter sweep
        wavsynth.set(M8WavsynthParam.RESONANCE, 0xC0)    # High resonance for 303-style sound
        wavsynth.set(M8WavsynthParam.AMP, 0x20)          # Amplifier level
        wavsynth.set(M8WavsynthParam.LIMIT, M8LimiterType.SIN)  # Sine wave limiter

        # Configure first modulator (ADSR) for volume envelope
        wavsynth.modulators[0].destination = M8WavsynthModDest.VOLUME

        # Configure second modulator (ADSR) for cutoff sweep
        wavsynth.modulators[1].destination = M8WavsynthModDest.CUTOFF
        default_amount = wavsynth.modulators[1].amount
        default_decay = wavsynth.modulators[1].get(4)
        wavsynth.modulators[1].amount = default_amount // 2
        wavsynth.modulators[1].set(4, default_decay // 2)

        print(f"  Instrument: {wavsynth.name} (shape={wave_name})")

        # Add instrument to project
        project.instruments[idx] = wavsynth

        # Create phrase with random notes (use different seed per phrase)
        phrase = M8Phrase()
        phrase_notes = []
        for step in range(16):
            # Choose random note from C3, C4, C5
            note = rng.choice(BASS_NOTES)
            phrase_notes.append(M8Note(note).name)

            # Create step with note and full velocity
            step_obj = M8PhraseStep(
                note=note,
                velocity=0x7F,  # Full velocity
                instrument=idx   # Use corresponding instrument
            )

            # Add Chance FX (CHA) with value 0x80
            step_obj.fx[0] = M8FXTuple(key=M8SequenceFX.CHA, value=0x80)

            phrase[step] = step_obj

        print(f"  Phrase: {', '.join(phrase_notes[:8])} ...")
        project.phrases[idx] = phrase

        # Create chain referencing the phrase
        chain = M8Chain()
        chain[0] = M8ChainStep(phrase=idx, transpose=0x00)
        project.chains[idx] = chain
        print(f"  Chain: references phrase 0x{idx:02X}")

    # Add all chains to song matrix (stacked vertically in track 0)
    print(f"\nArranging song: stacking 16 chains in track 0, rows 0-15")
    for row in range(16):
        project.song[row][0] = row  # Chain idx at row idx, track 0
        print(f"  Row {row:2d}: Chain 0x{row:02X}")

    return project


def save_project(project: M8Project):
    """Save the M8 project."""
    # Create output directory
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Write M8 project file
    output_path = OUTPUT_DIR / f"{PROJECT_NAME}.m8s"
    print(f"\nSaving project to {output_path}...")
    project.write_to_file(str(output_path))

    print(f"\n✓ Demo complete!")
    print(f"  Project: {output_path}")
    print(f"  Instruments: 16 wavsynth variations (0x00-0x0F) with different wave shapes")
    print(f"  Phrases: 16 unique patterns with random notes (C3/D#3/C4/D#4/C5) and Chance FX")
    print(f"  Chains: 16 chains stacked vertically in track 0")
    print(f"  Song: 16 rows x 1 track arrangement")


def main():
    """Main entry point."""
    project = create_wavsynth_303_project()
    save_project(project)


if __name__ == '__main__':
    main()
