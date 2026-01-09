#!/usr/bin/env python3

"""
Acid Banger 909 Chain Demo - Sample chain version with slice-based triggering

Creates a 16-row M8 project using a SINGLE sample chain with slice triggering:
- Vitling's acid-banger 909 pattern generators
- Random sample selection from Erica Pico sample packs
- All samples concatenated into one chain WAV with slice metadata
- Single sampler instrument using FILE slice mode (SLICE=0x01)
- Notes trigger slices: C-1=slice 0, C#1=slice 1, D-1=slice 2, etc.
- Random FX on hats (cut, reverse, retrigger)

Prerequisites:
- Download Erica Pico samples first: python demos/utils/download_erica_pico_samples.py
- Samples will be saved to tmp/erica-pico-samples/

Project structure:
- Row 0: songs 0x10,0x20,0x30 -> chains 0x10,0x20,0x30 -> phrases 0x10,0x20,0x30 -> instrument 0x00 (all)
- Row 1: songs 0x11,0x21,0x31 -> chains 0x11,0x21,0x31 -> phrases 0x11,0x21,0x31 -> instrument 0x00 (all)
- ... (continues for 16 rows total)
- Single chain sample with 48 slices (16 kicks + 16 snares + 16 hats)
"""

import random
import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple

from m8.api.project import M8Project
from m8.api.instruments.sampler import M8Sampler, M8SamplerParam
from m8.api.phrase import M8Phrase, M8PhraseStep, M8Note
from m8.api.chain import M8Chain, M8ChainStep
from m8.api.fx import M8FXTuple, M8SequenceFX, M8SamplerFX
from m8.tools.chain_builder import ChainBuilder

from demos.patterns.acid_909 import (
    get_random_kick_pattern,
    get_random_snare_pattern,
    get_random_hat_pattern
)


# Configuration
PROJECT_NAME = "ACID-BANG-909-CHAIN"
OUTPUT_DIR = Path("tmp/demos/acid_banger_909_chain")
SAMPLES_BASE = Path("tmp/erica-pico-samples")
BPM = 130
SEED = 42
NUM_ROWS = 16
NOTE_DIVISION = 4  # 4=16th notes (4 ticks per beat), 2=8th notes, 8=32nd notes
LENGTH_MULTIPLIER = 2  # Sample duration multiplier (allows ring-out)

# M8 constants
MAX_VELOCITY = 0x7F
SLICE_MODE_FILE = 0x01

# Slice organization: 16 kicks (0-15), 16 snares (16-31), 16 hats (32-47)
KICK_SLICE_OFFSET = 0
SNARE_SLICE_OFFSET = 16
HAT_SLICE_OFFSET = 32


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


def slice_index_to_note(slice_index: int) -> int:
    """Convert slice index to M8 note value.

    Slice 0 = C-1 (note value 0)
    Slice 1 = C#1 (note value 1)
    Slice 2 = D-1 (note value 2)
    etc.

    Args:
        slice_index: Slice index (0-255)

    Returns:
        M8 note value
    """
    return slice_index


def create_phrase_from_pattern(pattern: List[float], slice_index: int,
                                add_fx: bool = False, rng: random.Random = None) -> M8Phrase:
    """Create an M8 phrase from a pattern velocity list using slice triggering.

    Args:
        pattern: List of velocity floats (0.0-1.0)
        slice_index: Index of the slice in the chain (determines note)
        add_fx: If True, randomly add FX to some steps (for hats)
        rng: Random number generator for FX

    Returns:
        M8Phrase with notes triggering the specified slice
    """
    phrase = M8Phrase()
    note_value = slice_index_to_note(slice_index)

    for step_idx, velocity_float in enumerate(pattern):
        if velocity_float > 0.0:
            velocity_m8 = velocity_to_m8(velocity_float)

            step = M8PhraseStep(
                note=note_value,  # Note determines which slice to play
                velocity=velocity_m8,
                instrument=0x00   # Always use instrument 0 (the chain sampler)
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


def create_sample_chain(samples_by_type: Dict[str, List[Path]], rng: random.Random,
                       slice_duration_ms: float) -> Tuple[bytes, Dict[str, List[int]]]:
    """Create the sample chain WAV with slice metadata.

    Args:
        samples_by_type: Dict mapping type (kick/snare/hat) to sample paths
        rng: Random number generator for sample selection
        slice_duration_ms: Duration for each slice in milliseconds

    Returns:
        Tuple of (chain_wav_bytes, slice_mapping)
        slice_mapping is dict mapping type to list of slice indices
    """
    print(f"\nBuilding sample chain...")
    print(f"  Slice duration: {slice_duration_ms:.2f}ms")

    # Select samples for all rows
    selected_samples = []
    slice_mapping = {
        'kick': [],
        'snare': [],
        'hat': []
    }

    # Select kicks (slices 0-15)
    for i in range(NUM_ROWS):
        kick_sample = rng.choice(samples_by_type['kick'])
        selected_samples.append(kick_sample)
        slice_mapping['kick'].append(KICK_SLICE_OFFSET + i)
        print(f"  Kick {i:2d} (slice {KICK_SLICE_OFFSET + i:2d}): {kick_sample.name[:40]}")

    # Select snares (slices 16-31)
    for i in range(NUM_ROWS):
        snare_sample = rng.choice(samples_by_type['snare'])
        selected_samples.append(snare_sample)
        slice_mapping['snare'].append(SNARE_SLICE_OFFSET + i)
        print(f"  Snare {i:2d} (slice {SNARE_SLICE_OFFSET + i:2d}): {snare_sample.name[:40]}")

    # Select hats (slices 32-47)
    for i in range(NUM_ROWS):
        hat_sample = rng.choice(samples_by_type['hat'])
        selected_samples.append(hat_sample)
        slice_mapping['hat'].append(HAT_SLICE_OFFSET + i)
        print(f"  Hat {i:2d} (slice {HAT_SLICE_OFFSET + i:2d}): {hat_sample.name[:40]}")

    # Build chain using ChainBuilder (it handles all normalization/padding/fade)
    print(f"\nBuilding chain with ChainBuilder...")
    builder = ChainBuilder(
        slice_duration_ms=slice_duration_ms,
        fade_ms=3,
        frame_rate=44100
    )

    chain_wav_io, _ = builder.build_chain(selected_samples)
    chain_wav_bytes = chain_wav_io.getvalue()

    print(f"  Chain created: {len(chain_wav_bytes)} bytes")
    print(f"  Total slices: {len(selected_samples)}")

    return chain_wav_bytes, slice_mapping


def create_acid_banger_chain_project():
    """Create the full acid banger 909 chain M8 project."""
    print(f"Creating Acid Banger 909 Chain demo: {PROJECT_NAME}")
    print(f"BPM: {BPM}, Seed: {SEED}, Rows: {NUM_ROWS}")

    # Check if samples exist
    if not SAMPLES_BASE.exists():
        print(f"\n✗ Error: Sample directory not found: {SAMPLES_BASE.absolute()}")
        print(f"\nPlease download Erica Pico samples first:")
        print(f"  python demos/utils/download_erica_pico_samples.py")
        print(f"\nThis will download sample packs to: {SAMPLES_BASE.absolute()}")
        sys.exit(1)

    # Initialize RNG with seed
    rng = random.Random(SEED)

    # Find available samples
    print(f"\nScanning samples from: {SAMPLES_BASE.absolute()}")
    samples_by_type = find_samples_by_type(SAMPLES_BASE)

    print(f"Found samples:")
    print(f"  Kicks: {len(samples_by_type['kick'])}")
    print(f"  Snares: {len(samples_by_type['snare'])}")
    print(f"  Hats: {len(samples_by_type['hat'])}")

    if not all(samples_by_type.values()):
        print(f"\n✗ Error: Not enough samples found in all categories!")
        sys.exit(1)

    # Calculate slice duration: (60s / BPM) * 1000ms * (1 / note_division) * length_multiplier
    # At 130 BPM with note_division=4 and length_multiplier=2:
    #   beat = 461ms, tick = 115ms, slice_duration = 231ms
    beat_duration_ms = (60.0 / BPM) * 1000
    tick_duration_ms = beat_duration_ms / NOTE_DIVISION
    slice_duration_ms = tick_duration_ms * LENGTH_MULTIPLIER

    # Create sample chain (ChainBuilder handles all normalization/padding/fade)
    chain_wav_bytes, slice_mapping = create_sample_chain(
        samples_by_type, rng, slice_duration_ms
    )

    # Initialize project
    project = M8Project.initialise()
    project.metadata.name = PROJECT_NAME
    project.metadata.tempo = BPM
    project.metadata.directory = "/Songs/pym8-demos/acid-banger-909-chain/"

    # Create the single chain sampler instrument
    print(f"\nCreating chain sampler instrument...")
    chain_sampler = M8Sampler(name="CHAIN", sample_path="samples/chain.wav")
    chain_sampler.set(M8SamplerParam.SLICE, SLICE_MODE_FILE)
    project.instruments[0] = chain_sampler
    print(f"  Instrument 0: CHAIN (slice mode: FILE)")

    # Create 16 rows of patterns
    print(f"\nGenerating {NUM_ROWS} rows of patterns...")

    for row in range(NUM_ROWS):
        print(f"\n--- Row {row} ---")

        # Calculate indices for this row
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

        # Get slice indices for this row
        kick_slice = slice_mapping['kick'][row]
        snare_slice = slice_mapping['snare'][row]
        hat_slice = slice_mapping['hat'][row]

        # --- KICK CHANNEL ---
        kick_pattern_name, kick_pattern = get_random_kick_pattern(rng)
        kick_phrase = create_phrase_from_pattern(kick_pattern, kick_slice)
        project.phrases[phrase_kick] = kick_phrase

        kick_chain = M8Chain()
        kick_chain[0] = M8ChainStep(phrase=phrase_kick, transpose=0x00)
        project.chains[chain_kick] = kick_chain

        project.song[row][0] = song_kick

        print(f"  Kick   (slice {kick_slice:2d}): pattern={kick_pattern_name}")

        # --- SNARE CHANNEL ---
        snare_pattern_name, snare_pattern = get_random_snare_pattern(rng)
        snare_phrase = create_phrase_from_pattern(snare_pattern, snare_slice)
        project.phrases[phrase_snare] = snare_phrase

        snare_chain = M8Chain()
        snare_chain[0] = M8ChainStep(phrase=phrase_snare, transpose=0x00)
        project.chains[chain_snare] = snare_chain

        project.song[row][1] = song_snare

        print(f"  Snare  (slice {snare_slice:2d}): pattern={snare_pattern_name}")

        # --- HAT CHANNEL ---
        hat_pattern_name, hat_pattern = get_random_hat_pattern(rng)
        hat_phrase = create_phrase_from_pattern(hat_pattern, hat_slice, add_fx=True, rng=rng)
        project.phrases[phrase_hat] = hat_phrase

        hat_chain = M8Chain()
        hat_chain[0] = M8ChainStep(phrase=phrase_hat, transpose=0x00)
        project.chains[chain_hat] = hat_chain

        project.song[row][2] = song_hat

        print(f"  Hat    (slice {hat_slice:2d}): pattern={hat_pattern_name}")

    return project, chain_wav_bytes


def save_project(project: M8Project, chain_wav_bytes: bytes):
    """Save the M8 project and the chain WAV file."""
    # Create output directories
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    samples_dir = OUTPUT_DIR / "samples"
    samples_dir.mkdir(exist_ok=True)

    # Write M8 project file
    output_path = OUTPUT_DIR / f"{PROJECT_NAME}.m8s"
    print(f"\nSaving project to {output_path}...")
    project.write_to_file(str(output_path))

    # Write chain WAV file
    chain_path = samples_dir / "chain.wav"
    print(f"Saving chain sample to {chain_path}...")
    with open(chain_path, 'wb') as f:
        f.write(chain_wav_bytes)

    print(f"\n✓ Demo complete!")
    print(f"  Project: {output_path}")
    print(f"  Chain sample: {chain_path}")
    print(f"  Total instruments: 1 (chain sampler with 48 slices)")
    print(f"\nYou can now copy this to your M8 device using:")
    print(f"  python tools/copy_demos_to_m8.py")


def main():
    """Main entry point."""
    project, chain_wav_bytes = create_acid_banger_chain_project()
    save_project(project, chain_wav_bytes)


if __name__ == '__main__':
    main()
