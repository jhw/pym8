#!/usr/bin/env python

"""
Wavsynth 303 Demo - Acid bassline-style demo using M8 Wavsynth

Creates a simple M8 project with:
- Single wavsynth instrument with two ADSR modulators
- First modulator assigned to volume
- Second modulator assigned to cutoff with reduced level and decay
- 16-step phrase with random notes from C3, C4, C5
- Chance FX on each note for variation

Output: tmp/demos/wavsynth_303/WAVSYNTH-303.m8s
"""

import random
from pathlib import Path

from m8.api.project import M8Project
from m8.api.instruments.wavsynth import M8Wavsynth, M8WavsynthParam, M8WavShape, M8WavsynthModDest
from m8.api.phrase import M8Phrase, M8PhraseStep, M8Note
from m8.api.chain import M8Chain, M8ChainStep
from m8.api.fx import M8FXTuple, M8SequenceFX

# Configuration
PROJECT_NAME = "WAVSYNTH-303"
OUTPUT_DIR = Path("tmp/demos/wavsynth_303")
BPM = 135
SEED = 42

# Note choices for random bass pattern
BASS_NOTES = [M8Note.C_3, M8Note.C_4, M8Note.C_5]


def create_wavsynth_303_project():
    """Create the Wavsynth 303 M8 project."""
    print(f"Creating Wavsynth 303 demo: {PROJECT_NAME}")
    print(f"BPM: {BPM}, Seed: {SEED}")

    # Initialize RNG with seed for reproducible results
    rng = random.Random(SEED)

    # Initialize project
    project = M8Project.initialise()
    project.metadata.name = PROJECT_NAME
    project.metadata.tempo = BPM
    project.metadata.directory = "/Songs/pym8-demos/wavsynth-303/"

    # Create wavsynth instrument at slot 0x00
    wavsynth = M8Wavsynth(name="ACID-303")

    # Set synth parameters
    wavsynth.set(M8WavsynthParam.SHAPE, M8WavShape.SAW)  # Sawtooth wave for classic acid sound
    wavsynth.set(M8WavsynthParam.FILTER_TYPE, 0x01)  # Low Pass filter
    wavsynth.set(M8WavsynthParam.CUTOFF, 0x20)       # Low cutoff for filter sweep
    wavsynth.set(M8WavsynthParam.RESONANCE, 0xC0)    # High resonance for 303-style sound
    wavsynth.set(M8WavsynthParam.AMP, 0x20)          # Amplifier level
    wavsynth.set(M8WavsynthParam.LIMIT, 0x01)        # Limiter amount

    # Configure first modulator (ADSR) for volume envelope
    # Modulator 0 is already ADSR by default (type 0)
    wavsynth.modulators[0].destination = M8WavsynthModDest.VOLUME
    # Keep default ADSR values for volume (attack, hold, decay already set)

    # Configure second modulator (ADSR) for cutoff sweep
    # Modulator 1 is already ADSR by default (type 0)
    wavsynth.modulators[1].destination = M8WavsynthModDest.CUTOFF

    # Get default values
    default_amount = wavsynth.modulators[1].amount
    default_decay = wavsynth.modulators[1].get(4)  # Decay is at offset 4 for ADSR

    # Set to half the default values
    wavsynth.modulators[1].amount = default_amount // 2
    wavsynth.modulators[1].set(4, default_decay // 2)  # Decay

    print(f"  Modulator 1 (Volume): dest={M8WavsynthModDest.VOLUME}, amount={wavsynth.modulators[0].amount}")
    print(f"  Modulator 2 (Cutoff): dest={M8WavsynthModDest.CUTOFF}, amount={wavsynth.modulators[1].amount}, decay={wavsynth.modulators[1].get(4)}")

    # Add instrument to project
    project.instruments[0x00] = wavsynth

    # Create phrase with random notes
    phrase = M8Phrase()
    print(f"\n  Phrase pattern (16 steps):")
    for step in range(16):
        # Choose random note from C3, C4, C5
        note = rng.choice(BASS_NOTES)

        # Create step with note and full velocity
        step_obj = M8PhraseStep(
            note=note,
            velocity=0x7F,  # Full velocity
            instrument=0x00  # Use wavsynth at slot 0
        )

        # Add Chord FX (CHA) with value 0x80
        step_obj.fx[0] = M8FXTuple(key=M8SequenceFX.CHA, value=0x80)

        phrase[step] = step_obj

        # Print note name for visualization (find enum name from value)
        note_name = M8Note(note).name
        print(f"    Step {step:2d}: {note_name:5s} (CHA=0x80)")

    project.phrases[0x00] = phrase

    # Create chain referencing the phrase
    chain = M8Chain()
    chain[0] = M8ChainStep(phrase=0x00, transpose=0x00)
    project.chains[0x00] = chain

    # Add chain to song matrix
    project.song[0][0] = 0x00  # Chain 0 at row 0, track 0

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
    print(f"  Instrument: ACID-303 wavsynth with cutoff modulation")
    print(f"  Pattern: 16 random steps (C3/C4/C5) with Chance FX")


def main():
    """Main entry point."""
    project = create_wavsynth_303_project()
    save_project(project)


if __name__ == '__main__':
    main()
