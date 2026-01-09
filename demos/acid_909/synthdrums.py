#!/usr/bin/env python3

"""
Acid Synthdrums 909 Demo - Algorithmic 909 drum patterns with DW01 synthdrums

Creates a 16-row M8 project with kick, snare, and hat patterns using:
- Vitling's acid-banger 909 pattern generators
- Random FM Synth drum selection from DW01 synthdrums pack
- Random FX on hats (retrigger)

Prerequisites:
- Extract DW01 synthdrums to YAML first:
  python demos/utils/extract_m8i_to_yaml.py --type 4
- Instruments will be loaded from tmp/dw01-synthdrums/yaml/

Project structure:
- Row 0: songs 0x10,0x20,0x30 -> chains 0x10,0x20,0x30 -> phrases 0x10,0x20,0x30 -> instruments 0x00,0x01,0x02
- Row 1: songs 0x11,0x21,0x31 -> chains 0x11,0x21,0x31 -> phrases 0x11,0x21,0x31 -> instruments 0x03,0x04,0x05
- ... (continues for 16 rows total)

Instrument categorization:
- Kick: Any instrument with "KICK" in the name
- Hat: Any instrument with "HAT" in the name
- Snare: Everything else (snares, claps, toms, percussion, etc.)

Note: This demo uses 909-style drum patterns with FM synthesis drums.
"""

import random
import sys
import argparse
from pathlib import Path
from typing import Dict, List

from m8.api.project import M8Project
from m8.api.phrase import M8Phrase, M8PhraseStep, M8Note
from m8.api.chain import M8Chain, M8ChainStep
from m8.api.fx import M8FXTuple, M8SequenceFX

from demos.lib.preset_yaml import load_presets_yaml
from demos.patterns.acid_909 import (
    get_random_kick_pattern,
    get_random_snare_pattern,
    get_random_hat_pattern
)


# Configuration
PROJECT_NAME = "ACID-SYNTHDRUMS-909"
OUTPUT_DIR = Path("tmp/demos/acid_synthdrums_909")
SYNTHDRUMS_YAML_DEFAULT = Path("tmp/dw01-synthdrums/yaml")
BPM = 130
SEED = 42
NUM_ROWS = 16

# M8 constants
MAX_VELOCITY = 0x7F


def categorize_instruments(presets: Dict[str, any]) -> Dict[str, List[tuple]]:
    """Categorize loaded instruments by type (kick, hat, snare).

    Args:
        presets: Dict mapping preset names to instrument instances

    Returns:
        Dict with 'kick', 'hat', 'snare' keys, each containing list of (name, instrument) tuples
    """
    categorized = {
        'kick': [],
        'hat': [],
        'snare': []
    }

    for name, instrument in presets.items():
        name_upper = name.upper()

        # Categorize by name pattern matching
        if 'KICK' in name_upper:
            categorized['kick'].append((name, instrument))
        elif 'HAT' in name_upper:
            categorized['hat'].append((name, instrument))
        else:
            # Everything else is snare (includes snares, claps, toms, percussion, etc.)
            categorized['snare'].append((name, instrument))

    return categorized


def velocity_to_m8(velocity_float: float) -> int:
    """Convert float velocity (0.0-1.0) to M8 velocity (0x00-0x7F).

    Zero velocities are kept as zero (no hit).
    """
    if velocity_float == 0.0:
        return 0x00
    return int(velocity_float * MAX_VELOCITY)


def create_phrase_from_pattern(pattern: List[float], instrument_idx: int,
                                add_fx: bool = False, rng: random.Random = None) -> M8Phrase:
    """Create an M8 phrase from a pattern velocity list.

    Args:
        pattern: List of velocity floats (0.0-1.0)
        instrument_idx: M8 instrument index (0x00-0xFF)
        add_fx: If True, randomly add FX to some steps (for hats)
        rng: Random number generator for FX
    """
    phrase = M8Phrase()

    for step_idx, velocity_float in enumerate(pattern):
        if velocity_float > 0.0:
            velocity_m8 = velocity_to_m8(velocity_float)

            step = M8PhraseStep(
                note=M8Note.C_4,
                velocity=velocity_m8,
                instrument=instrument_idx
            )

            # Add random FX for hats (retrigger only - synthdrums don't need cut/reverse)
            if add_fx and rng:
                fx_roll = rng.random()
                if fx_roll < 0.33:
                    # Retrigger (RET)
                    step.fx[0] = M8FXTuple(key=M8SequenceFX.RET, value=0x40)
                # else: 67% chance of no FX

            phrase[step_idx] = step

    return phrase


def create_acid_synthdrums_project(synthdrums_yaml_dir: Path):
    """Create the full acid synthdrums 909 M8 project."""
    print(f"Creating Acid Synthdrums 909 demo: {PROJECT_NAME}")
    print(f"BPM: {BPM}, Seed: {SEED}, Rows: {NUM_ROWS}")

    # Check if YAML directory exists
    if not synthdrums_yaml_dir.exists():
        print(f"\n✗ Error: Synthdrums YAML directory not found: {synthdrums_yaml_dir.absolute()}")
        print(f"\nPlease extract DW01 synthdrums to YAML first:")
        print(f"  python demos/utils/extract_m8i_to_yaml.py --type 4")
        print(f"\nThis will create YAML files in: {synthdrums_yaml_dir.absolute()}")
        sys.exit(1)

    # Initialize RNG with seed
    rng = random.Random(SEED)

    # Load all synthdrums instruments from YAML
    print(f"\nLoading instruments from: {synthdrums_yaml_dir.absolute()}")
    presets = load_presets_yaml(synthdrums_yaml_dir)

    if not presets:
        print(f"\n✗ Error: No YAML presets found in {synthdrums_yaml_dir.absolute()}")
        print(f"\nPlease extract DW01 synthdrums to YAML first:")
        print(f"  python demos/utils/extract_m8i_to_yaml.py --type 4")
        sys.exit(1)

    # Categorize instruments by type
    instruments_by_type = categorize_instruments(presets)

    print(f"Found instruments:")
    print(f"  Kicks: {len(instruments_by_type['kick'])}")
    print(f"  Hats: {len(instruments_by_type['hat'])}")
    print(f"  Snares: {len(instruments_by_type['snare'])}")

    if not all(instruments_by_type.values()):
        print(f"\n✗ Error: Not enough instruments found in all categories!")
        print(f"  Kicks: {len(instruments_by_type['kick'])}")
        print(f"  Hats: {len(instruments_by_type['hat'])}")
        print(f"  Snares: {len(instruments_by_type['snare'])}")
        print(f"\nPlease ensure DW01 synthdrums are extracted with all types:")
        print(f"  python demos/utils/extract_m8i_to_yaml.py --type 4")
        sys.exit(1)

    # Initialize project
    project = M8Project.initialise()
    project.metadata.name = PROJECT_NAME
    project.metadata.tempo = BPM
    project.metadata.directory = "/Songs/pym8-demos/acid-synthdrums-909/"

    # Create 16 rows
    print(f"\nGenerating {NUM_ROWS} rows of patterns...")

    for row in range(NUM_ROWS):
        print(f"\n--- Row {row} ---")

        # Calculate indices for this row
        # Row 0: songs 0x10,0x20,0x30; Row 1: songs 0x11,0x21,0x31; etc.
        song_kick = 0x10 + row
        song_snare = 0x20 + row
        song_hat = 0x30 + row

        # Same for chains and phrases (one-to-one mapping)
        chain_kick = song_kick
        chain_snare = song_snare
        chain_hat = song_hat

        phrase_kick = song_kick
        phrase_snare = song_snare
        phrase_hat = song_hat

        # Instruments increment sequentially
        inst_kick = row * 3
        inst_snare = row * 3 + 1
        inst_hat = row * 3 + 2

        # --- KICK CHANNEL ---
        # Pick random kick instrument
        kick_name, kick_instrument = rng.choice(instruments_by_type['kick'])

        # Generate kick pattern
        kick_pattern_name, kick_pattern = get_random_kick_pattern(rng)

        # Clone and assign kick instrument
        kick_inst = kick_instrument.clone()
        kick_inst.name = f"K{row:X}"
        project.instruments[inst_kick] = kick_inst

        # Create kick phrase
        kick_phrase = create_phrase_from_pattern(kick_pattern, inst_kick)
        project.phrases[phrase_kick] = kick_phrase

        # Create kick chain
        kick_chain = M8Chain()
        kick_chain[0] = M8ChainStep(phrase=phrase_kick, transpose=0x00)
        project.chains[chain_kick] = kick_chain

        # Add to song matrix
        project.song[row][0] = song_kick

        print(f"  Kick   [{inst_kick:02X}]: {kick_name[:30]:30s} pattern={kick_pattern_name}")

        # --- SNARE CHANNEL ---
        # Pick random snare instrument
        snare_name, snare_instrument = rng.choice(instruments_by_type['snare'])

        # Generate snare pattern
        snare_pattern_name, snare_pattern = get_random_snare_pattern(rng)

        # Clone and assign snare instrument
        snare_inst = snare_instrument.clone()
        snare_inst.name = f"S{row:X}"
        project.instruments[inst_snare] = snare_inst

        # Create snare phrase
        snare_phrase = create_phrase_from_pattern(snare_pattern, inst_snare)
        project.phrases[phrase_snare] = snare_phrase

        # Create snare chain
        snare_chain = M8Chain()
        snare_chain[0] = M8ChainStep(phrase=phrase_snare, transpose=0x00)
        project.chains[chain_snare] = snare_chain

        # Add to song matrix
        project.song[row][1] = song_snare

        print(f"  Snare  [{inst_snare:02X}]: {snare_name[:30]:30s} pattern={snare_pattern_name}")

        # --- HAT CHANNEL ---
        # Pick random hat instrument
        hat_name, hat_instrument = rng.choice(instruments_by_type['hat'])

        # Generate hat pattern
        hat_pattern_name, hat_pattern = get_random_hat_pattern(rng)

        # Clone and assign hat instrument
        hat_inst = hat_instrument.clone()
        hat_inst.name = f"H{row:X}"
        project.instruments[inst_hat] = hat_inst

        # Create hat phrase with random FX
        hat_phrase = create_phrase_from_pattern(hat_pattern, inst_hat, add_fx=True, rng=rng)
        project.phrases[phrase_hat] = hat_phrase

        # Create hat chain
        hat_chain = M8Chain()
        hat_chain[0] = M8ChainStep(phrase=phrase_hat, transpose=0x00)
        project.chains[chain_hat] = hat_chain

        # Add to song matrix
        project.song[row][2] = song_hat

        print(f"  Hat    [{inst_hat:02X}]: {hat_name[:30]:30s} pattern={hat_pattern_name}")

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
    print(f"  Total instruments: {NUM_ROWS * 3}")
    print(f"\nYou can now copy this to your M8 device using:")
    print(f"  python tools/copy_demos_to_m8.py")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Generate Acid Synthdrums 909 demo with DW01 synthdrums'
    )
    parser.add_argument(
        '--synthdrums-yaml',
        type=Path,
        default=SYNTHDRUMS_YAML_DEFAULT,
        help=f'Path to synthdrums YAML directory (default: {SYNTHDRUMS_YAML_DEFAULT})'
    )

    args = parser.parse_args()

    project = create_acid_synthdrums_project(args.synthdrums_yaml)
    save_project(project)


if __name__ == '__main__':
    main()
