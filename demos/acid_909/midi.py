#!/usr/bin/env python3

"""
Acid 909 MIDI Demo - Acid banger 909 drum patterns via External MIDI

Creates a 16-row M8 project with kick, snare, and hat patterns using:
- Vitling's acid-banger 909 pattern generators
- External MIDI instruments (for hardware drum machines)

Project structure:
- Row 0: songs 0x10,0x20,0x30 -> chains 0x10,0x20,0x30 -> phrases 0x10,0x20,0x30
- Row 1: songs 0x11,0x21,0x31 -> chains 0x11,0x21,0x31 -> phrases 0x11,0x21,0x31
- ... (continues for 16 rows total)
- 3 External instruments: kick (ch1), snare (ch2), hat (ch3)

All notes are C-4 (standard drum trigger note).

Output: tmp/demos/acid_909_midi/ACID-909-MIDI.m8s
"""

import argparse
import random
from pathlib import Path
from typing import List

from m8.api.project import M8Project
from m8.api.instruments.external import (
    M8External, M8ExternalParam, M8ExternalInput, M8ExternalPort
)
from m8.api.instrument import M8LimiterType
from m8.api.phrase import M8Phrase, M8PhraseStep, M8Note
from m8.api.chain import M8Chain, M8ChainStep
from m8.api.fx import M8FXTuple, M8SequenceFX

from demos.patterns.acid_909 import (
    get_random_kick_pattern,
    get_random_snare_pattern,
    get_random_hat_pattern
)


# Configuration
PROJECT_NAME = "ACID-909-MIDI"
OUTPUT_DIR = Path("tmp/demos/acid_909/midi")
BPM = 130
SEED = 42
NUM_ROWS = 16

# M8 constants
MAX_VELOCITY = 0x7F
DRUM_NOTE = M8Note.C_4  # Standard drum trigger note


def velocity_to_m8(velocity_float: float) -> int:
    """Convert float velocity (0.0-1.0) to M8 velocity (0x00-0x7F)."""
    if velocity_float == 0.0:
        return 0x00
    return int(velocity_float * MAX_VELOCITY)


def create_external_instrument(name: str, midi_channel: int) -> M8External:
    """Create an External instrument configured for MIDI output.

    Args:
        name: Instrument name
        midi_channel: MIDI channel (1-16)

    Returns:
        M8External configured for MIDI drum output
    """
    inst = M8External()
    inst.name = name

    # MIDI output settings
    inst.set(M8ExternalParam.PORT, M8ExternalPort.MIDI)
    inst.set(M8ExternalParam.CHANNEL, midi_channel)
    inst.set(M8ExternalParam.BANK, 0)
    inst.set(M8ExternalParam.PROGRAM, 0)

    # Audio input settings
    inst.set(M8ExternalParam.INPUT, M8ExternalInput.LINE_IN_L)

    # Mixer settings
    inst.set(M8ExternalParam.AMP, 0x20)
    inst.set(M8ExternalParam.LIMIT, M8LimiterType.SIN)

    return inst


def create_phrase_from_pattern(pattern: List[float], instrument_idx: int) -> M8Phrase:
    """Create an M8 phrase from a pattern velocity list.

    Args:
        pattern: List of velocity floats (0.0-1.0)
        instrument_idx: M8 instrument index

    Returns:
        M8Phrase with C-4 notes at pattern hits
    """
    phrase = M8Phrase()

    for step_idx, velocity_float in enumerate(pattern):
        if velocity_float > 0.0:
            velocity_m8 = velocity_to_m8(velocity_float)

            step = M8PhraseStep(
                note=DRUM_NOTE,
                velocity=velocity_m8,
                instrument=instrument_idx
            )
            phrase[step_idx] = step

    return phrase


def create_acid_909_midi_project(kick_channel: int, snare_channel: int, hat_channel: int):
    """Create the Acid 909 MIDI M8 project."""
    print(f"Creating Acid 909 MIDI demo: {PROJECT_NAME}")
    print(f"BPM: {BPM}, Seed: {SEED}, Rows: {NUM_ROWS}")
    print(f"MIDI Channels: Kick={kick_channel}, Snare={snare_channel}, Hat={hat_channel}")

    # Initialize RNG with seed
    rng = random.Random(SEED)

    # Initialize project
    project = M8Project.initialise()
    project.metadata.name = PROJECT_NAME
    project.metadata.tempo = BPM
    project.metadata.directory = "/Songs/pym8-demos/acid-909-midi/"

    # Create the three external instruments (shared across all rows)
    kick_inst = create_external_instrument("KICK", kick_channel)
    snare_inst = create_external_instrument("SNARE", snare_channel)
    hat_inst = create_external_instrument("HAT", hat_channel)

    project.instruments[0x00] = kick_inst
    project.instruments[0x01] = snare_inst
    project.instruments[0x02] = hat_inst

    print(f"\nCreated 3 External MIDI instruments:")
    print(f"  [00] KICK  -> MIDI channel {kick_channel}")
    print(f"  [01] SNARE -> MIDI channel {snare_channel}")
    print(f"  [02] HAT   -> MIDI channel {hat_channel}")

    # Create 16 rows
    print(f"\nGenerating {NUM_ROWS} rows of acid 909 patterns...")

    for row in range(NUM_ROWS):
        print(f"\n--- Row {row} ---")

        # Calculate indices for this row
        song_kick = 0x10 + row
        song_snare = 0x20 + row
        song_hat = 0x30 + row

        chain_kick = song_kick
        chain_snare = song_snare
        chain_hat = song_hat

        phrase_kick = song_kick
        phrase_snare = song_snare
        phrase_hat = song_hat

        # --- KICK ---
        kick_pattern_name, kick_pattern = get_random_kick_pattern(rng)
        kick_phrase = create_phrase_from_pattern(kick_pattern, 0x00)
        project.phrases[phrase_kick] = kick_phrase

        kick_chain = M8Chain()
        kick_chain[0] = M8ChainStep(phrase=phrase_kick, transpose=0x00)
        project.chains[chain_kick] = kick_chain
        project.song[row][0] = song_kick

        print(f"  Kick:  {kick_pattern_name}")

        # --- SNARE ---
        snare_pattern_name, snare_pattern = get_random_snare_pattern(rng)
        snare_phrase = create_phrase_from_pattern(snare_pattern, 0x01)
        project.phrases[phrase_snare] = snare_phrase

        snare_chain = M8Chain()
        snare_chain[0] = M8ChainStep(phrase=phrase_snare, transpose=0x00)
        project.chains[chain_snare] = snare_chain
        project.song[row][1] = song_snare

        print(f"  Snare: {snare_pattern_name}")

        # --- HAT ---
        hat_pattern_name, hat_pattern = get_random_hat_pattern(rng)
        hat_phrase = create_phrase_from_pattern(hat_pattern, 0x02)
        project.phrases[phrase_hat] = hat_phrase

        hat_chain = M8Chain()
        hat_chain[0] = M8ChainStep(phrase=phrase_hat, transpose=0x00)
        project.chains[chain_hat] = hat_chain
        project.song[row][2] = song_hat

        print(f"  Hat:   {hat_pattern_name}")

    return project


def save_project(project: M8Project):
    """Save the M8 project."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    output_path = OUTPUT_DIR / f"{PROJECT_NAME}.m8s"
    print(f"\nSaving project to {output_path}...")
    project.validate()
    project.write_to_file(str(output_path))

    print(f"\n✓ Demo complete!")
    print(f"  Project: {output_path}")
    print(f"  Instruments: 3 External MIDI (kick, snare, hat)")
    print(f"  Patterns: Vitling's acid-banger 909 algorithm")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Generate acid 909 drum patterns via External MIDI"
    )
    parser.add_argument(
        "--kick-channel", type=int, default=1,
        help="MIDI channel for kick (1-16, default: 1)"
    )
    parser.add_argument(
        "--snare-channel", type=int, default=2,
        help="MIDI channel for snare (1-16, default: 2)"
    )
    parser.add_argument(
        "--hat-channel", type=int, default=3,
        help="MIDI channel for hat (1-16, default: 3)"
    )

    args = parser.parse_args()

    # Validate channels
    for name, ch in [("kick", args.kick_channel), ("snare", args.snare_channel), ("hat", args.hat_channel)]:
        if not 1 <= ch <= 16:
            parser.error(f"{name}-channel must be between 1 and 16")

    project = create_acid_909_midi_project(
        args.kick_channel,
        args.snare_channel,
        args.hat_channel
    )
    save_project(project)


if __name__ == '__main__':
    main()
