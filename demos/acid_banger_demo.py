#!/usr/bin/env python

"""
Acid Banger Demo - Algorithmic drum patterns inspired by vitling's acid-banger

Creates a 16-row M8 project with kick, snare, and hat patterns using:
- Vitling's acid-banger pattern generators
- Random sample selection from Erica Pico sample packs
- Random FX on hats (cut, reverse, retrigger)

Project structure:
- Row 0: songs 0x10,0x20,0x30 -> chains 0x10,0x20,0x30 -> phrases 0x10,0x20,0x30 -> instruments 0x00,0x01,0x02
- Row 1: songs 0x11,0x21,0x31 -> chains 0x11,0x21,0x31 -> phrases 0x11,0x21,0x31 -> instruments 0x03,0x04,0x05
- ... (continues for 16 rows total)
"""

import random
import shutil
import re
from pathlib import Path
from typing import Dict, List

from m8.api.project import M8Project
from m8.api.sampler import M8Sampler
from m8.api.phrase import M8Phrase, M8PhraseStep
from m8.api.chain import M8Chain, M8ChainStep
from m8.api.fx import M8FXTuple, M8SequenceFX, M8SamplerFX

from acid_banger_patterns import (
    get_random_kick_pattern,
    get_random_snare_pattern,
    get_random_hat_pattern
)


# Configuration
PROJECT_NAME = "ACID-BANGER"
OUTPUT_DIR = Path("tmp/demos/acid_banger")
SAMPLES_BASE = Path("/Users/jhw/work/gists/music/6014d1500bd8089900b63af39e6d7d8d/tmp/samples/erica-pico")
BPM = 130
SEED = 42
NUM_ROWS = 16

# M8 constants
NOTE_C4 = 0x24
MAX_VELOCITY = 0x7F


def find_samples_by_type(samples_dir: Path) -> Dict[str, List[Path]]:
    """Categorize all .wav samples by type (kick, snare, hat)."""
    samples = {
        'kick': [],
        'snare': [],
        'hat': []
    }

    # Find all wav files
    wav_files = list(samples_dir.glob("**/*.wav"))

    for wav_file in wav_files:
        filename_lower = wav_file.name.lower()

        # Categorize by pattern matching
        if re.search(r'(kick|kk|bd)', filename_lower):
            samples['kick'].append(wav_file)
        elif re.search(r'(snare|sn|clap|cl)', filename_lower):
            samples['snare'].append(wav_file)
        elif re.search(r'(hat|hh)', filename_lower):
            samples['hat'].append(wav_file)

    return samples


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
                note=NOTE_C4,
                velocity=velocity_m8,
                instrument=instrument_idx
            )

            # Add random FX for hats (25% chance each of cut, reverse, retrigger)
            if add_fx and rng:
                fx_roll = rng.random()
                if fx_roll < 0.25:
                    # Cut (LEN)
                    step.fx[0] = M8FXTuple(key=M8SamplerFX.LEN, value=0xC0)
                elif fx_roll < 0.50:
                    # Reverse (PLY)
                    step.fx[0] = M8FXTuple(key=M8SamplerFX.PLY, value=0x01)
                elif fx_roll < 0.75:
                    # Retrigger (RET)
                    step.fx[0] = M8FXTuple(key=M8SequenceFX.RET, value=0x40)
                # else: 25% chance of no FX

            phrase[step_idx] = step

    return phrase


def create_acid_banger_project():
    """Create the full acid banger M8 project."""
    print(f"Creating Acid Banger demo: {PROJECT_NAME}")
    print(f"BPM: {BPM}, Seed: {SEED}, Rows: {NUM_ROWS}")

    # Initialize RNG with seed
    rng = random.Random(SEED)

    # Find available samples
    print(f"\nScanning samples from: {SAMPLES_BASE}")
    samples_by_type = find_samples_by_type(SAMPLES_BASE)

    print(f"Found samples:")
    print(f"  Kicks: {len(samples_by_type['kick'])}")
    print(f"  Snares: {len(samples_by_type['snare'])}")
    print(f"  Hats: {len(samples_by_type['hat'])}")

    if not all(samples_by_type.values()):
        raise ValueError("Not enough samples found in all categories!")

    # Initialize project
    project = M8Project.initialise()
    project.metadata.name = PROJECT_NAME
    project.metadata.tempo = BPM
    project.metadata.directory = "/Songs/pym8-demos/acid-banger/"

    # Track which samples we're using (for copying later)
    used_samples: Dict[int, Path] = {}  # instrument_idx -> sample_path

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
        # Pick random kick sample
        kick_sample = rng.choice(samples_by_type['kick'])
        kick_sample_rel = f"samples/{kick_sample.name}"
        used_samples[inst_kick] = kick_sample

        # Generate kick pattern
        kick_pattern_name, kick_pattern = get_random_kick_pattern(rng)

        # Create kick instrument
        kick_sampler = M8Sampler(name=f"K{row:X}", sample_path=kick_sample_rel)
        project.instruments[inst_kick] = kick_sampler

        # Create kick phrase
        kick_phrase = create_phrase_from_pattern(kick_pattern, inst_kick)
        project.phrases[phrase_kick] = kick_phrase

        # Create kick chain
        kick_chain = M8Chain()
        kick_chain[0] = M8ChainStep(phrase=phrase_kick, transpose=0x00)
        project.chains[chain_kick] = kick_chain

        # Add to song matrix
        project.song[row][0] = song_kick

        print(f"  Kick   [{inst_kick:02X}]: {kick_sample.name[:30]:30s} pattern={kick_pattern_name}")

        # --- SNARE CHANNEL ---
        # Pick random snare sample
        snare_sample = rng.choice(samples_by_type['snare'])
        snare_sample_rel = f"samples/{snare_sample.name}"
        used_samples[inst_snare] = snare_sample

        # Generate snare pattern
        snare_pattern_name, snare_pattern = get_random_snare_pattern(rng)

        # Create snare instrument
        snare_sampler = M8Sampler(name=f"S{row:X}", sample_path=snare_sample_rel)
        project.instruments[inst_snare] = snare_sampler

        # Create snare phrase
        snare_phrase = create_phrase_from_pattern(snare_pattern, inst_snare)
        project.phrases[phrase_snare] = snare_phrase

        # Create snare chain
        snare_chain = M8Chain()
        snare_chain[0] = M8ChainStep(phrase=phrase_snare, transpose=0x00)
        project.chains[chain_snare] = snare_chain

        # Add to song matrix
        project.song[row][1] = song_snare

        print(f"  Snare  [{inst_snare:02X}]: {snare_sample.name[:30]:30s} pattern={snare_pattern_name}")

        # --- HAT CHANNEL ---
        # Pick random hat sample
        hat_sample = rng.choice(samples_by_type['hat'])
        hat_sample_rel = f"samples/{hat_sample.name}"
        used_samples[inst_hat] = hat_sample

        # Generate hat pattern
        hat_pattern_name, hat_pattern = get_random_hat_pattern(rng)

        # Create hat instrument
        hat_sampler = M8Sampler(name=f"H{row:X}", sample_path=hat_sample_rel)
        project.instruments[inst_hat] = hat_sampler

        # Create hat phrase with random FX
        hat_phrase = create_phrase_from_pattern(hat_pattern, inst_hat, add_fx=True, rng=rng)
        project.phrases[phrase_hat] = hat_phrase

        # Create hat chain
        hat_chain = M8Chain()
        hat_chain[0] = M8ChainStep(phrase=phrase_hat, transpose=0x00)
        project.chains[chain_hat] = hat_chain

        # Add to song matrix
        project.song[row][2] = song_hat

        print(f"  Hat    [{inst_hat:02X}]: {hat_sample.name[:30]:30s} pattern={hat_pattern_name}")

    return project, used_samples


def save_project(project: M8Project, used_samples: Dict[int, Path]):
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
    for inst_idx, sample_path in used_samples.items():
        dest = samples_dir / sample_path.name
        if not dest.exists():
            shutil.copy2(sample_path, dest)
            print(f"  {sample_path.name}")

    print(f"\n✓ Demo complete!")
    print(f"  Project: {output_path}")
    print(f"  Samples: {samples_dir}")
    print(f"  Total instruments: {len(used_samples)}")
    print(f"\nYou can now copy this to your M8 device using:")
    print(f"  python tools/copy_demos_to_m8.py")


def main():
    """Main entry point."""
    project, used_samples = create_acid_banger_project()
    save_project(project, used_samples)


if __name__ == '__main__':
    main()
