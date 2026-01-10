#!/usr/bin/env python3

"""
Wavsynth 303 Demo - Algorithmic TB-303 acid basslines using M8 Wavsynth

Creates a 16-row M8 project with TB-303 style acid basslines using:
- Vitling's acid-banger 303 pattern generators
- 16 different Wavsynth shapes (pulse, saw, wavetables)
- Probability-based note triggering with accent and glide
- 64-step patterns (4 phrases of 16 steps each)

Original algorithm from:
https://github.com/vitling/acid-banger

Project structure:
- Row 0: chain 0x00 -> phrases 0x00-0x03 -> instrument 0x00 (PULSE12)
- Row 1: chain 0x01 -> phrases 0x04-0x07 -> instrument 0x01 (PULSE25)
- ... (continues for 16 rows total, each with different wave shape)

Output: tmp/demos/wavsynth_303/WAVSYNTH-303.m8s
"""

import random
from typing import List
import yaml
from pathlib import Path

from m8.api.project import M8Project
from m8.api.instruments.wavsynth import M8Wavsynth, M8WavsynthParam, M8WavShape
from m8.api.phrase import M8Phrase, M8PhraseStep, M8Note
from m8.api.chain import M8Chain, M8ChainStep
from m8.api.fx import M8FXTuple, M8SequenceFX

from demos.patterns.acid_303 import get_random_303_pattern, AcidPattern

# Configuration
PROJECT_NAME = "WAVSYNTH-303"
OUTPUT_DIR = Path("tmp/demos/acid_303/wavsynth")
BPM = 135
SEED = 42
NUM_ROWS = 16
STEPS_PER_PHRASE = 16
PHRASES_PER_CHAIN = 4
TOTAL_STEPS = STEPS_PER_PHRASE * PHRASES_PER_CHAIN  # 64 steps

# M8 constants
MAX_VELOCITY = 0x7F

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

# 303-style Wavsynth preset (human-readable YAML with enum names)
PRESET_303_YAML = """
# M8 Wavsynth Preset - 303-style Acid Bass
# This preset demonstrates human-readable YAML serialization with enum names
# instead of opaque integer values.

name: AC-BASS
params:
  TRANSPOSE: 0
  TABLE_TICK: 0
  VOLUME: 0
  PITCH: 0
  FINE_TUNE: 128
  SHAPE: PULSE12           # Waveform shape - readable enum name instead of integer
  SIZE: 32
  MULT: 0
  WARP: 0
  MIRROR: 0
  FILTER_TYPE: LOWPASS     # Filter type - readable enum name
  CUTOFF: 32               # Low cutoff for filter sweep
  RESONANCE: 192           # High resonance for 303-style sound
  AMP: 32
  LIMIT: SIN               # Limiter type - readable enum name
  PAN: 128
  DRY: 192
  CHORUS_SEND: 192
  DELAY_SEND: 128
  REVERB_SEND: 0

# Modulators with readable type and parameter names
# Only the two AHD envelopes are active - the remaining 2 slots use defaults
modulators:
- type: AHD_ENVELOPE       # Readable modulator type
  destination: VOLUME      # Volume envelope
  amount: 255
  params:
    ATTACK: 0
    HOLD: 0
    DECAY: 128

- type: AHD_ENVELOPE       # Second envelope for cutoff sweep
  destination: CUTOFF      # Cutoff modulation
  amount: 127
  params:
    ATTACK: 0
    HOLD: 0
    DECAY: 64
"""


def velocity_to_m8(velocity_float: float) -> int:
    """Convert float velocity (0.0-1.0) to M8 velocity (0x00-0x7F)."""
    if velocity_float == 0.0:
        return 0x00
    return int(velocity_float * MAX_VELOCITY)


def create_phrases_from_303_pattern(pattern: AcidPattern, instrument_idx: int,
                                    base_phrase_idx: int) -> List[M8Phrase]:
    """Create 4 M8 phrases (16 steps each) from a 64-step 303 pattern.

    Args:
        pattern: AcidPattern with 64 steps
        instrument_idx: M8 instrument index
        base_phrase_idx: Starting phrase index

    Returns:
        List of 4 M8Phrase objects
    """
    phrases = []

    for phrase_num in range(PHRASES_PER_CHAIN):
        phrase = M8Phrase()
        start_step = phrase_num * STEPS_PER_PHRASE

        for local_step in range(STEPS_PER_PHRASE):
            global_step = start_step + local_step
            note_value = pattern.notes[global_step]

            if note_value is not None:
                velocity_m8 = velocity_to_m8(pattern.velocities[global_step])

                step = M8PhraseStep(
                    note=note_value,
                    velocity=velocity_m8,
                    instrument=instrument_idx
                )

                # Add glide FX if marked
                if pattern.glides[global_step]:
                    step.fx[0] = M8FXTuple(key=M8SequenceFX.TSP, value=0x80)

                phrase[local_step] = step

        phrases.append(phrase)

    return phrases


def load_base_303_wavsynth():
    """Load the base 303-style wavsynth instrument from inline YAML preset.

    The template contains human-readable enum names like PULSE12, LOWPASS, etc.
    Individual variations clone this and modify the wave shape.

    Returns:
        M8Wavsynth configured with 303-style parameters from YAML
    """
    # Load preset from inline YAML string
    preset_dict = yaml.safe_load(PRESET_303_YAML)
    return M8Wavsynth.from_dict(preset_dict)


def create_wavsynth_303_project():
    """Create the Wavsynth 303 M8 project with 16 acid banger patterns."""
    print(f"Creating Wavsynth 303 demo: {PROJECT_NAME}")
    print(f"BPM: {BPM}, Seed: {SEED}")
    print(f"Pattern length: {TOTAL_STEPS} steps ({PHRASES_PER_CHAIN} phrases x {STEPS_PER_PHRASE} steps)")

    # Initialize RNG with seed for reproducible results
    rng = random.Random(SEED)

    # Initialize project
    project = M8Project.initialise()
    project.metadata.name = PROJECT_NAME
    project.metadata.tempo = BPM
    project.metadata.directory = "/Songs/pym8-demos/wavsynth-303/"

    # Load base 303-style wavsynth template from inline YAML preset
    base_wavsynth = load_base_303_wavsynth()
    print(f"\nLoaded base preset from inline YAML")

    # Create 16 rows of 303 patterns, each with different wave shape
    print(f"\nGenerating {NUM_ROWS} rows of 303 acid basslines...")

    for row in range(NUM_ROWS):
        print(f"\n--- Row {row} (0x{row:X}) ---")

        # Get wave shape for this row's instrument
        wave_shape = WAVE_SHAPES[row]
        wave_name = wave_shape.name

        # Clone and customize instrument
        wavsynth = base_wavsynth.clone()
        wavsynth.name = f"AC-{wave_name[:8]}"
        wavsynth.set(M8WavsynthParam.SHAPE, wave_shape)
        project.instruments[row] = wavsynth

        print(f"Instrument: {wavsynth.name} (shape={wave_name})")

        # Generate random root note for this pattern (C2 to C4 range)
        root_note = rng.choice(range(12, 37))  # C2 to C4
        root_note_name = M8Note(root_note).name

        # Generate 64-step acid banger 303 pattern
        pattern_name, pattern = get_random_303_pattern(rng, length=TOTAL_STEPS, root_note=root_note)

        # Count active notes
        active_notes = sum(1 for n in pattern.notes if n is not None)
        glide_count = sum(1 for g in pattern.glides if g)

        print(f"Pattern: {pattern_name} (root={root_note_name})")
        print(f"  Notes: {active_notes}/{TOTAL_STEPS}, Glides: {glide_count}")

        # Create phrases from pattern
        base_phrase_idx = row * PHRASES_PER_CHAIN
        phrases = create_phrases_from_303_pattern(pattern, row, base_phrase_idx)

        for i, phrase in enumerate(phrases):
            phrase_idx = base_phrase_idx + i
            project.phrases[phrase_idx] = phrase

        # Create chain referencing the 4 phrases
        chain = M8Chain()
        for i in range(PHRASES_PER_CHAIN):
            chain[i] = M8ChainStep(phrase=base_phrase_idx + i, transpose=0x00)
        project.chains[row] = chain

        print(f"Chain 0x{row:02X} -> phrases 0x{base_phrase_idx:02X}-0x{base_phrase_idx + 3:02X}")

        # Add chain to song
        project.song[row][0] = row

    return project


def save_project(project: M8Project):
    """Save the M8 project."""
    # Create output directory
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Write M8 project file
    output_path = OUTPUT_DIR / f"{PROJECT_NAME}.m8s"
    print(f"\nSaving project to {output_path}...")
    project.validate()
    project.write_to_file(str(output_path))

    print(f"\n✓ Demo complete!")
    print(f"  Project: {output_path}")
    print(f"  Instruments: 16 wavsynth variations with different wave shapes")
    print(f"  Patterns: Vitling's acid-banger 303 algorithm (64 steps each)")
    print(f"  Song: 16 rows x 1 track arrangement")


def main():
    """Main entry point."""
    project = create_wavsynth_303_project()
    save_project(project)


if __name__ == '__main__':
    main()
