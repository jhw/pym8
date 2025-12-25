#!/usr/bin/env python

"""
Acid Banger 303 Demo - Algorithmic TB-303 acid basslines inspired by vitling's acid-banger

Creates a 16-row M8 project with TB-303 style acid basslines using:
- Vitling's acid-banger 303 pattern generators
- Authentic 303 VCO samples (SAW and SQR waveforms)
- Probability-based note triggering with accent and glide
- 64-step patterns (4 phrases of 16 steps each)

Original algorithm from:
https://github.com/vitling/acid-banger

Project structure:
- Row 0: chain 0x00 -> phrases 0x01-0x04 -> instrument 0x00 (SAW)
- Row 1: chain 0x01 -> phrases 0x05-0x08 -> instrument 0x01 (SQR)
- Row 2: chain 0x02 -> phrases 0x09-0x0C -> instrument 0x00 (SAW)
- ... (continues alternating for 16 rows total)

Each chain contains 4 phrases of 16 steps (64 total steps) with a single 303 pattern
distributed across all phrases.

Output: tmp/demos/acid_banger_303/ACID-BANGER-303.m8s
"""

import random
import shutil
from pathlib import Path
from typing import Dict, List

from m8.api.project import M8Project
from m8.api.instruments.sampler import M8Sampler
from m8.api.phrase import M8Phrase, M8PhraseStep, M8Note
from m8.api.chain import M8Chain, M8ChainStep
from m8.api.fx import M8FXTuple, M8SequenceFX
from preset_yaml import load_preset_yaml

from acid_banger_303_patterns import get_random_303_pattern, AcidPattern


# Configuration
PROJECT_NAME = "ACID-BANGER-303"
OUTPUT_DIR = Path("tmp/demos/acid_banger_303")
SAMPLES_BASE = Path("demos/samples")
BPM = 130
SEED = 42
NUM_ROWS = 16
STEPS_PER_PHRASE = 16
PHRASES_PER_CHAIN = 4
TOTAL_STEPS = STEPS_PER_PHRASE * PHRASES_PER_CHAIN  # 64 steps

# M8 constants
MAX_VELOCITY = 0x7F

# 303 samples (must exist in demos/samples/)
SAMPLE_303_SAW = "303 VCO SAW.wav"
SAMPLE_303_SQR = "303 VCO SQR.wav"


def velocity_to_m8(velocity_float: float) -> int:
    """Convert float velocity (0.0-1.0) to M8 velocity (0x00-0x7F).

    Zero velocities are kept as zero (no hit).
    """
    if velocity_float == 0.0:
        return 0x00
    return int(velocity_float * MAX_VELOCITY)


def create_phrases_from_303_pattern(pattern: AcidPattern, instrument_idx: int,
                                    base_phrase_idx: int) -> List[M8Phrase]:
    """Create 4 M8 phrases (16 steps each) from a 64-step 303 pattern.

    Args:
        pattern: AcidPattern with 64 steps
        instrument_idx: M8 instrument index (0x00 or 0x01)
        base_phrase_idx: Starting phrase index (e.g., 0x01 for phrases 0x01-0x04)

    Returns:
        List of 4 M8Phrase objects
    """
    phrases = []

    for phrase_num in range(PHRASES_PER_CHAIN):
        phrase = M8Phrase()

        # Calculate step range for this phrase
        start_step = phrase_num * STEPS_PER_PHRASE
        end_step = start_step + STEPS_PER_PHRASE

        for local_step in range(STEPS_PER_PHRASE):
            global_step = start_step + local_step

            # Get note from pattern
            note_value = pattern.notes[global_step]

            if note_value is not None:
                velocity_m8 = velocity_to_m8(pattern.velocities[global_step])

                step = M8PhraseStep(
                    note=note_value,
                    velocity=velocity_m8,
                    instrument=instrument_idx
                )

                # Add glide/slide FX if marked (TSP command for portamento/glide)
                if pattern.glides[global_step]:
                    # TSP (transpose/pitch slide) - value 0x80 is smooth glide
                    step.fx[0] = M8FXTuple(key=M8SequenceFX.TSP, value=0x80)

                phrase[local_step] = step

        phrases.append(phrase)

    return phrases


def load_base_303_sampler(sample_name: str) -> M8Sampler:
    """Load the base 303-style sampler instrument from YAML preset.

    This loads the template instrument from demos/sampler_303_bass.yaml,
    which contains human-readable enum names and 303-optimized parameters.

    Args:
        sample_name: Name of the sample file (e.g., "303 VCO SAW.wav")

    Returns:
        M8Sampler configured with 303-style parameters from YAML
    """
    preset_path = Path(__file__).parent / "sampler_303_bass.yaml"
    sampler = load_preset_yaml(M8Sampler, preset_path)

    # Update sample path
    sampler.sample_path = f"samples/{sample_name}"

    return sampler


def create_acid_banger_303_project():
    """Create the full acid banger 303 M8 project."""
    print(f"Creating Acid Banger 303 demo: {PROJECT_NAME}")
    print(f"BPM: {BPM}, Seed: {SEED}, Rows: {NUM_ROWS}")
    print(f"Pattern length: {TOTAL_STEPS} steps ({PHRASES_PER_CHAIN} phrases x {STEPS_PER_PHRASE} steps)")

    # Initialize RNG with seed
    rng = random.Random(SEED)

    # Initialize project
    project = M8Project.initialise()
    project.metadata.name = PROJECT_NAME
    project.metadata.tempo = BPM
    project.metadata.directory = "/Songs/pym8-demos/acid-banger-303/"

    # Create the two base instruments (SAW and SQR)
    print(f"\nCreating base instruments:")

    # Instrument 0x00: 303 SAW
    saw_sampler = load_base_303_sampler(SAMPLE_303_SAW)
    saw_sampler.name = "303-SAW"
    project.instruments[0x00] = saw_sampler
    print(f"  [00] 303-SAW using {SAMPLE_303_SAW}")

    # Instrument 0x01: 303 SQR
    sqr_sampler = load_base_303_sampler(SAMPLE_303_SQR)
    sqr_sampler.name = "303-SQR"
    project.instruments[0x01] = sqr_sampler
    print(f"  [01] 303-SQR using {SAMPLE_303_SQR}")

    # Track which samples we're using (for copying later)
    used_samples = {
        SAMPLE_303_SAW: SAMPLES_BASE / SAMPLE_303_SAW,
        SAMPLE_303_SQR: SAMPLES_BASE / SAMPLE_303_SQR,
    }

    # Create 16 rows of 303 patterns
    print(f"\nGenerating {NUM_ROWS} rows of 303 acid basslines...")

    for row in range(NUM_ROWS):
        print(f"\n--- Row {row} (0x{row:X}) ---")

        # Calculate indices for this row
        # Row 0: chain 0x00, phrases 0x01-0x04, instrument 0x00
        # Row 1: chain 0x01, phrases 0x05-0x08, instrument 0x01
        # Row 2: chain 0x02, phrases 0x09-0x0C, instrument 0x00 (reuse)
        # etc.

        chain_idx = row  # 0x00, 0x01, 0x02, ...
        base_phrase_idx = (row * PHRASES_PER_CHAIN) + 1  # 0x01, 0x05, 0x09, ...

        # Alternate between the two instruments
        instrument_idx = row % 2  # 0x00 or 0x01
        instrument_name = "303-SAW" if instrument_idx == 0 else "303-SQR"

        # Generate random root note for this pattern (C2 to C4 range)
        # M8Note: C_1=0, so C_2=12, C_3=24, C_4=36
        root_note = rng.choice(range(12, 37))  # C2 to C4
        root_note_name = M8Note(root_note).name

        # Generate 64-step 303 pattern
        pattern_name, pattern = get_random_303_pattern(rng, length=TOTAL_STEPS, root_note=root_note)

        # Count active notes
        note_count = sum(1 for n in pattern.notes if n is not None)
        accent_count = sum(pattern.accents)
        glide_count = sum(pattern.glides)

        print(f"  Pattern: {pattern_name}, root={root_note_name}, notes={note_count}/{TOTAL_STEPS}, "
              f"accents={accent_count}, glides={glide_count}")
        print(f"  Instrument: [{instrument_idx:02X}] {instrument_name}")

        # Create 4 phrases from the 64-step pattern
        phrases = create_phrases_from_303_pattern(pattern, instrument_idx, base_phrase_idx)

        # Add phrases to project
        for i, phrase in enumerate(phrases):
            phrase_idx = base_phrase_idx + i
            project.phrases[phrase_idx] = phrase
            print(f"    Phrase 0x{phrase_idx:02X}: steps {i*16}-{(i+1)*16-1}")

        # Create chain with 4 steps pointing to the 4 phrases
        chain = M8Chain()
        for i in range(PHRASES_PER_CHAIN):
            phrase_idx = base_phrase_idx + i
            chain[i] = M8ChainStep(phrase=phrase_idx, transpose=0x00)

        project.chains[chain_idx] = chain
        print(f"  Chain 0x{chain_idx:02X}: phrases 0x{base_phrase_idx:02X}-0x{base_phrase_idx+3:02X}")

        # Add to song matrix (track 0, row N)
        project.song[row][0] = chain_idx
        print(f"  Song[{row}][0] = 0x{chain_idx:02X}")

    return project, used_samples


def save_project(project: M8Project, used_samples: Dict[str, Path]):
    """Save the M8 project and copy all used samples."""
    # Create output directories
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    samples_dir = OUTPUT_DIR / "samples"
    samples_dir.mkdir(exist_ok=True)

    # Write M8 project file
    output_path = OUTPUT_DIR / f"{PROJECT_NAME}.m8s"
    print(f"\nSaving project to {output_path}...")
    project.write_to_file(str(output_path))

    # Copy all used samples
    print(f"\nCopying {len(used_samples)} samples to {samples_dir}...")
    for sample_name, sample_path in used_samples.items():
        dest = samples_dir / sample_name
        if not dest.exists():
            shutil.copy2(sample_path, dest)
            print(f"  {sample_name}")

    print(f"\n✓ Demo complete!")
    print(f"  Project: {output_path}")
    print(f"  Samples: {samples_dir}")
    print(f"  Pattern style: Vitling's acid-banger 303 algorithm")
    print(f"  Total rows: {NUM_ROWS}")
    print(f"  Steps per pattern: {TOTAL_STEPS} ({PHRASES_PER_CHAIN} x {STEPS_PER_PHRASE})")


def main():
    """Main entry point."""
    project, used_samples = create_acid_banger_303_project()
    save_project(project, used_samples)


if __name__ == '__main__':
    main()
