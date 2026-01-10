#!/usr/bin/env python3

"""
Macrosynth 303 Demo - Algorithmic TB-303 acid basslines using M8 Macrosynth

Creates a 16-row M8 project with TB-303 style acid basslines using:
- Vitling's acid-banger 303 pattern generators
- 16 different Macrosynth shapes (Braids algorithms)
- Probability-based note triggering with accent and glide
- 64-step patterns (4 phrases of 16 steps each)

Original algorithm from:
https://github.com/vitling/acid-banger

Project structure:
- Row 0: chain 0x00 -> phrases 0x00-0x03 -> instrument 0x00 (CSAW)
- Row 1: chain 0x01 -> phrases 0x04-0x07 -> instrument 0x01 (MORPH)
- ... (continues for 16 rows total, each with different Braids shape)

Output: tmp/demos/macrosynth_303/MACROSYNTH-303.m8s
"""

import random
from typing import List
import yaml
from pathlib import Path

from m8.api.project import M8Project
from m8.api.instruments.macrosynth import M8Macrosynth, M8MacrosynthParam, M8MacroShape
from m8.api.phrase import M8Phrase, M8PhraseStep, M8Note
from m8.api.chain import M8Chain, M8ChainStep
from m8.api.fx import M8FXTuple, M8SequenceFX

from demos.patterns.acid_303 import get_random_303_pattern, AcidPattern

# Configuration
PROJECT_NAME = "MACROSYNTH-303"
OUTPUT_DIR = Path("tmp/demos/acid_303/macrosynth")
BPM = 135
SEED = 42
NUM_ROWS = 16
STEPS_PER_PHRASE = 16
PHRASES_PER_CHAIN = 4
TOTAL_STEPS = STEPS_PER_PHRASE * PHRASES_PER_CHAIN  # 64 steps

# M8 constants
MAX_VELOCITY = 0x7F

# Macro shapes for each of the 16 instruments (variety of Braids algorithms)
MACRO_SHAPES = [
    M8MacroShape.CSAW,       # 0x00 - CS80-like sawtooth
    M8MacroShape.MORPH,      # 0x01 - Variable wave morphing
    M8MacroShape.SAW_SQUARE, # 0x02 - Sawtooth/square morphing
    M8MacroShape.FOLD,       # 0x03 - Waveform folding
    M8MacroShape.RING,       # 0x04 - Ring modulation
    M8MacroShape.SAW_STACK,  # 0x05 - Supersaw
    M8MacroShape.VOSM,       # 0x06 - Vowel synthesis
    M8MacroShape.FM,         # 0x07 - FM synthesis
    M8MacroShape.FBFM,       # 0x08 - Feedback FM
    M8MacroShape.PLUK,       # 0x09 - Plucked string
    M8MacroShape.BOWD,       # 0x0A - Bowed string
    M8MacroShape.BELL,       # 0x0B - Bell
    M8MacroShape.DRUM,       # 0x0C - Metallic drum
    M8MacroShape.KICK,       # 0x0D - Kick drum
    M8MacroShape.WTBL,       # 0x0E - Wavetable
    M8MacroShape.CLOU,       # 0x0F - Granular cloud
]

# 303-style Macrosynth preset (human-readable YAML with enum names)
PRESET_303_YAML = """
# M8 Macrosynth Preset - 303-style Acid Bass
# This preset demonstrates human-readable YAML serialization with enum names
# instead of opaque integer values.

name: AC-BASS
params:
  TRANSPOSE: 0
  TABLE_TICK: 0
  VOLUME: 0
  PITCH: 0
  FINE_TUNE: 128
  SHAPE: CSAW              # Oscillator shape - CS80-like sawtooth
  TIMBRE: 128              # Timbre control (synthesis parameter 1)
  COLOUR: 128              # Colour control (synthesis parameter 2)
  DEGRADE: 0               # Bitcrusher/degradation amount
  REDUX: 0                 # Sample rate reduction amount
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


def load_base_303_macrosynth():
    """Load the base 303-style macrosynth instrument from inline YAML preset.

    The template contains human-readable enum names like CSAW, LOWPASS, etc.
    Individual variations clone this and modify the oscillator shape.

    Returns:
        M8Macrosynth configured with 303-style parameters from YAML
    """
    # Load preset from inline YAML string
    preset_dict = yaml.safe_load(PRESET_303_YAML)
    return M8Macrosynth.from_dict(preset_dict)


def create_macrosynth_303_project():
    """Create the Macrosynth 303 M8 project with 16 acid banger patterns."""
    print(f"Creating Macrosynth 303 demo: {PROJECT_NAME}")
    print(f"BPM: {BPM}, Seed: {SEED}")
    print(f"Pattern length: {TOTAL_STEPS} steps ({PHRASES_PER_CHAIN} phrases x {STEPS_PER_PHRASE} steps)")

    # Initialize RNG with seed for reproducible results
    rng = random.Random(SEED)

    # Initialize project
    project = M8Project.initialise()
    project.metadata.name = PROJECT_NAME
    project.metadata.tempo = BPM
    project.metadata.directory = "/Songs/pym8-demos/macrosynth-303/"

    # Load base 303-style macrosynth template from inline YAML preset
    base_macrosynth = load_base_303_macrosynth()
    print(f"\nLoaded base preset from inline YAML")

    # Create 16 rows of 303 patterns, each with different Braids shape
    print(f"\nGenerating {NUM_ROWS} rows of 303 acid basslines...")

    for row in range(NUM_ROWS):
        print(f"\n--- Row {row} (0x{row:X}) ---")

        # Get macro shape for this row's instrument
        macro_shape = MACRO_SHAPES[row]
        shape_name = macro_shape.name

        # Clone and customize instrument
        macrosynth = base_macrosynth.clone()
        macrosynth.name = f"AC-{shape_name[:8]}"
        macrosynth.set(M8MacrosynthParam.SHAPE, macro_shape)
        project.instruments[row] = macrosynth

        print(f"Instrument: {macrosynth.name} (shape={shape_name})")

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
    print(f"  Instruments: 16 macrosynth variations with different Braids shapes")
    print(f"  Patterns: Vitling's acid-banger 303 algorithm (64 steps each)")
    print(f"  Song: 16 rows x 1 track arrangement")


def main():
    """Main entry point."""
    project = create_macrosynth_303_project()
    save_project(project)


if __name__ == '__main__':
    main()
