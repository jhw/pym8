#!/usr/bin/env python3

"""
Macrosynth 303 Demo - Acid bassline-style demo using M8 Macrosynth

This demo demonstrates loading instrument presets from human-readable inline YAML.
The base 303 preset uses readable enum names like:
- SHAPE: CSAW (instead of integer 0)
- FILTER_TYPE: LOWPASS (instead of integer 1)
- Modulator type: AHD_ENVELOPE (instead of integer 0)
- LFO SHAPE: TRI, TRIGGER_MODE: FREE (instead of integers)

Creates an M8 project with:
- 16 macrosynth instruments (0x00-0x0F), each with a different Braids shape
- Base preset loaded from YAML, then cloned and customized
- 16 phrases (0x00-0x0F), each with different random note patterns
- 16 chains (0x00-0x0F), each referencing the corresponding phrase
- Song arrangement: all 16 chains stacked vertically in track 0

Output: tmp/demos/macrosynth_303/MACROSYNTH-303.m8s
"""

import random
import yaml
from pathlib import Path

from m8.api.project import M8Project
from m8.api.instruments.macrosynth import M8Macrosynth, M8MacrosynthParam, M8MacroShape
from m8.api.phrase import M8Phrase, M8PhraseStep, M8Note
from m8.api.chain import M8Chain, M8ChainStep
from m8.api.fx import M8FXTuple, M8SequenceFX

# Configuration
PROJECT_NAME = "MACROSYNTH-303"
OUTPUT_DIR = Path("tmp/demos/macrosynth_303")
BPM = 135
SEED = 42

# Note choices for random bass pattern (C and D# at octaves 3 and 4, plus C5)
BASS_NOTES = [M8Note.C_3, M8Note.DS_3, M8Note.C_4, M8Note.DS_4, M8Note.C_5]

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
    """Create the Macrosynth 303 M8 project with 16 variations."""
    print(f"Creating Macrosynth 303 demo: {PROJECT_NAME}")
    print(f"BPM: {BPM}, Seed: {SEED}")
    print(f"Creating 16 instruments, phrases, and chains (0x00-0x0F)")

    # Initialize RNG with seed for reproducible results
    rng = random.Random(SEED)

    # Initialize project
    project = M8Project.initialise()
    project.metadata.name = PROJECT_NAME
    project.metadata.tempo = BPM
    project.metadata.directory = "/Songs/pym8-demos/macrosynth-303/"

    # Load base 303-style macrosynth template from inline YAML preset
    # This demonstrates loading presets with human-readable enum names
    base_macrosynth = load_base_303_macrosynth()
    print(f"\nLoaded base preset from inline YAML")
    print(f"  Preset demonstrates human-readable YAML with enum names:")
    print(f"    SHAPE: {M8MacroShape(base_macrosynth.get(M8MacrosynthParam.SHAPE)).name}")
    print(f"    FILTER_TYPE: LOWPASS, LIMIT: SIN")
    print(f"    Modulators: 2x AHD_ENVELOPE (volume & cutoff sweep)")

    # Create 16 variations (0x00-0x0F) by cloning and changing oscillator shape
    for idx in range(16):
        print(f"\n[{idx:02X}] Creating variation {idx + 1}/16")

        # Get macro shape for this instrument
        macro_shape = MACRO_SHAPES[idx]
        shape_name = macro_shape.name

        # Clone the base instrument
        macrosynth = base_macrosynth.clone()

        # Customize name and oscillator shape for this variation
        macrosynth.name = f"AC-{shape_name[:8]}"
        macrosynth.set(M8MacrosynthParam.SHAPE, macro_shape)

        print(f"  Instrument: {macrosynth.name} (shape={shape_name})")

        # Add instrument to project
        project.instruments[idx] = macrosynth

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
    print(f"  Base preset: Loaded from inline YAML (human-readable with enum names)")
    print(f"  Instruments: 16 macrosynth variations (0x00-0x0F) with different Braids shapes")
    print(f"  Phrases: 16 unique patterns with random notes (C3/D#3/C4/D#4/C5) and Chance FX")
    print(f"  Chains: 16 chains stacked vertically in track 0")
    print(f"  Song: 16 rows x 1 track arrangement")


def main():
    """Main entry point."""
    project = create_macrosynth_303_project()
    save_project(project)


if __name__ == '__main__':
    main()
