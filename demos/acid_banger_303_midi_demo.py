#!/usr/bin/env python3

"""
Acid Banger 303 MIDI Demo - Algorithmic TB-303 acid basslines via External MIDI

Creates a 16-row M8 project with TB-303 style acid basslines using:
- Vitling's acid-banger 303 pattern generators (exact algorithm from pattern.ts)
- External MIDI instrument (for Roland TB-03 or similar)
- Probability-based note triggering with accent and glide
- 64-step patterns (4 phrases of 16 steps each)
- Configurable OFF note insertion for MIDI note-off messages

Original algorithm from:
https://github.com/vitling/acid-banger

Note Distribution (from acid-banger):
- Steps divisible by 4: 60% trigger probability
- Steps divisible by 3: 50% trigger probability
- Even steps: 30% trigger probability
- Odd steps: 10% trigger probability

Velocity & Accent:
- MIDI Note On messages include velocity (0-127)
- M8 External instruments send phrase velocity as MIDI velocity
- Base velocity: 0.7-1.0 (89-127 in MIDI terms)
- Accented notes (30% chance): velocity boosted by 1.2x (capped at 127)

OFF Notes:
- Required for MIDI to send explicit note-off messages
- Probability controlled via --off-prob CLI argument
- Placed at random position between notes (never consecutive OFF notes)

Project structure:
- Row 0: chain 0x00 -> phrases 0x01-0x04 -> instrument 0x00 (EXTERNAL)
- Row 1: chain 0x01 -> phrases 0x05-0x08 -> instrument 0x00 (EXTERNAL)
- ... (continues for 16 rows total)

Each chain contains 4 phrases of 16 steps (64 total steps) with a single 303 pattern
distributed across all phrases.

Output: tmp/demos/acid_banger_303_midi/ACID-303-MIDI.m8s

================================================================================
ROLAND TB-03 SETUP INSTRUCTIONS
================================================================================

Before running this demo, configure your TB-03 as follows:

1. SET MIDI CLOCK TO USB (External Sync)
   -------------------------------------
   The TB-03 must sync to MIDI clock from the M8, not its internal clock.

   - Hold down the [FUNCTION] button
   - Turn the [VALUE] knob to select "SYnC"
   - Release the [FUNCTION] button to see current setting
   - Turn the [VALUE] knob to select "USB" (for USB connection)
     or "Auto" (auto-detect clock source)
   - Press the [FUNCTION] button to exit

   Sync source options:
     Int  = INTERNAL (ignores external clock)
     Auto = AUTO (syncs automatically if clock detected)
     USB  = USB (sync to USB port - requires firmware 1.06+)

   Note: Check firmware version by holding button 1 while powering on.
   Update to 1.06+ for USB sync option.

2. SET MIDI CHANNEL
   -----------------
   Set the TB-03 to receive on the same MIDI channel as configured in this demo
   (default channel 1, or specify with --channel argument).

   - Hold down the [FUNCTION] button
   - Turn the [VALUE] knob to select "CH"
   - Release the [FUNCTION] button to see current setting
   - Turn the [VALUE] knob to select your desired channel (1-16)
   - Press the [FUNCTION] button to exit

   Note: TB-03 defaults to MIDI channel 2.

3. SELECT A PATTERN
   -----------------
   Use the TRACK knob to select different patterns/tracks.

   - Turn the [TRACK] knob to select the desired track (1-7)
   - Each track can hold a different pattern

4. CLEAR THE CURRENT PATTERN
   --------------------------
   The TB-03's internal sequencer should be empty, otherwise it will play
   its own notes on top of what the M8 sends.

   - Press and hold the pattern button you want to clear
   - While holding, press the [PATTERN CLEAR] button
   - The pattern is now cleared

   TIP: Clear all patterns or use an empty track so the internal sequencer
   doesn't interfere with MIDI input.

Reference: Roland TB-03 Owner's Manual (PDF)
           https://static.roland.com/assets/media/pdf/TB-03_eng03_W.pdf
================================================================================
"""

import argparse
import random
from pathlib import Path

from m8.api.project import M8Project
from m8.api.instruments.external import (
    M8External, M8ExternalParam, M8ExternalInput, M8ExternalPort
)
from m8.api.instrument import M8LimiterType
from m8.api.phrase import M8Phrase, M8PhraseStep, M8Note, OFF_NOTE
from m8.api.chain import M8Chain, M8ChainStep
from m8.api.fx import M8FXTuple, M8SequenceFX

from acid_banger_303_patterns import get_random_303_pattern, AcidPattern


# Configuration
PROJECT_NAME = "ACID-303-MIDI"
OUTPUT_DIR = Path("tmp/demos/acid_banger_303_midi")
BPM = 130
SEED = 42
NUM_ROWS = 16
STEPS_PER_PHRASE = 16
PHRASES_PER_CHAIN = 4
TOTAL_STEPS = STEPS_PER_PHRASE * PHRASES_PER_CHAIN  # 64 steps

# M8 constants
MAX_VELOCITY = 0x7F


def velocity_to_m8(velocity_float: float) -> int:
    """Convert float velocity (0.0-1.0) to M8 velocity (0x00-0x7F).

    Zero velocities are kept as zero (no hit).
    """
    if velocity_float == 0.0:
        return 0x00
    return int(velocity_float * MAX_VELOCITY)


def add_off_notes_to_pattern(pattern: AcidPattern, rng: random.Random,
                             off_probability: float) -> list[int]:
    """Determine where to place OFF notes in the pattern.

    For MIDI instruments, we need explicit note-off messages. This function
    decides where to place them based on the off_probability.

    Rules:
    - Only place an OFF note if the probability check passes
    - OFF note goes at a random step between the current note and the next note
    - Never place two consecutive OFF notes
    - If two notes are on consecutive steps, no OFF note can be placed between them

    Args:
        pattern: AcidPattern with notes
        rng: Random number generator
        off_probability: Probability (0.0-1.0) of inserting an OFF note after each note

    Returns:
        List of step indices where OFF notes should be placed
    """
    off_note_steps = []
    length = len(pattern.notes)

    # Find all note positions
    note_positions = [i for i, n in enumerate(pattern.notes) if n is not None]

    for idx, note_pos in enumerate(note_positions):
        # Skip if probability check fails
        if rng.random() >= off_probability:
            continue

        # Find the next note position (or end of pattern)
        if idx + 1 < len(note_positions):
            next_note_pos = note_positions[idx + 1]
        else:
            # Wrap around to consider the pattern as looping
            next_note_pos = length

        # Calculate the gap between this note and the next
        gap_start = note_pos + 1
        gap_end = next_note_pos

        # Need at least 1 step gap to place an OFF note
        if gap_end - gap_start < 1:
            continue

        # Choose a random position in the gap
        off_pos = rng.randint(gap_start, gap_end - 1)

        # Don't place OFF if we already have one at the previous step
        if off_note_steps and off_note_steps[-1] == off_pos - 1:
            continue

        off_note_steps.append(off_pos)

    return off_note_steps


def create_phrases_from_303_pattern(pattern: AcidPattern, instrument_idx: int,
                                    base_phrase_idx: int, rng: random.Random,
                                    off_probability: float) -> list[M8Phrase]:
    """Create 4 M8 phrases (16 steps each) from a 64-step 303 pattern.

    Args:
        pattern: AcidPattern with 64 steps
        instrument_idx: M8 instrument index (0x00)
        base_phrase_idx: Starting phrase index (e.g., 0x01 for phrases 0x01-0x04)
        rng: Random number generator for off-note placement
        off_probability: Probability of inserting OFF notes (0.0-1.0)

    Returns:
        List of 4 M8Phrase objects
    """
    # Determine OFF note positions
    off_note_steps = add_off_notes_to_pattern(pattern, rng, off_probability)
    off_note_set = set(off_note_steps)

    phrases = []

    for phrase_num in range(PHRASES_PER_CHAIN):
        phrase = M8Phrase()

        # Calculate step range for this phrase
        start_step = phrase_num * STEPS_PER_PHRASE

        for local_step in range(STEPS_PER_PHRASE):
            global_step = start_step + local_step

            # Check for OFF note at this position
            if global_step in off_note_set:
                step = M8PhraseStep(
                    note=OFF_NOTE,
                    instrument=instrument_idx
                )
                phrase[local_step] = step
                continue

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


def create_external_instrument(name: str, midi_channel: int) -> M8External:
    """Create an External instrument configured for TB-03 MIDI output.

    Args:
        name: Instrument name
        midi_channel: MIDI channel (1-16)

    Returns:
        M8External configured for TB-03
    """
    inst = M8External()
    inst.name = name

    # MIDI output settings
    inst.set(M8ExternalParam.PORT, M8ExternalPort.MIDI)  # Hardware MIDI output
    inst.set(M8ExternalParam.CHANNEL, midi_channel - 1)  # M8 uses 0-indexed channels
    inst.set(M8ExternalParam.BANK, 0)
    inst.set(M8ExternalParam.PROGRAM, 0)

    # Audio input settings (for processing TB-03 audio through M8)
    inst.set(M8ExternalParam.INPUT, M8ExternalInput.LINE_IN_L)

    # Mixer settings
    inst.set(M8ExternalParam.AMP, 0x20)  # Amp level 32
    inst.set(M8ExternalParam.LIMIT, M8LimiterType.SIN)  # Limiter type SIN

    return inst


def create_acid_banger_303_midi_project(midi_channel: int, off_probability: float):
    """Create the full acid banger 303 MIDI M8 project.

    Args:
        midi_channel: MIDI channel for external instrument (1-16)
        off_probability: Probability (0.0-1.0) of inserting OFF notes after each note
    """
    print(f"Creating Acid Banger 303 MIDI demo: {PROJECT_NAME}")
    print(f"BPM: {BPM}, Seed: {SEED}, Rows: {NUM_ROWS}")
    print(f"MIDI Channel: {midi_channel}")
    print(f"OFF note probability: {off_probability:.0%}")
    print(f"Pattern length: {TOTAL_STEPS} steps ({PHRASES_PER_CHAIN} phrases x {STEPS_PER_PHRASE} steps)")

    # Initialize RNG with seed
    rng = random.Random(SEED)

    # Initialize project
    project = M8Project.initialise()
    project.metadata.name = PROJECT_NAME
    project.metadata.tempo = BPM
    project.metadata.directory = "/Songs/pym8-demos/acid-banger-303-midi/"

    # Create the external instrument for TB-03
    print(f"\nCreating external instrument:")
    external = create_external_instrument("TB-03", midi_channel)
    project.instruments[0x00] = external
    print(f"  [00] TB-03 on MIDI channel {midi_channel}")
    print(f"       Port: MIDI, Input: LINE_IN_L, AMP: 0x20, LIMIT: SIN")

    # Create 16 rows of 303 patterns
    print(f"\nGenerating {NUM_ROWS} rows of 303 acid basslines...")

    for row in range(NUM_ROWS):
        print(f"\n--- Row {row} (0x{row:X}) ---")

        # Calculate indices for this row
        chain_idx = row  # 0x00, 0x01, 0x02, ...
        base_phrase_idx = (row * PHRASES_PER_CHAIN) + 1  # 0x01, 0x05, 0x09, ...

        # All rows use the same external instrument
        instrument_idx = 0x00

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
        print(f"  Instrument: [{instrument_idx:02X}] TB-03")

        # Create 4 phrases from the 64-step pattern (with off-note insertion)
        phrases = create_phrases_from_303_pattern(
            pattern, instrument_idx, base_phrase_idx, rng, off_probability
        )

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

    return project


def save_project(project: M8Project):
    """Save the M8 project."""
    # Create output directory
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Write M8 project file
    output_path = OUTPUT_DIR / f"{PROJECT_NAME}.m8s"
    print(f"\nSaving project to {output_path}...")
    project.write_to_file(str(output_path))

    print(f"\n Demo complete!")
    print(f"  Project: {output_path}")
    print(f"  Pattern style: Vitling's acid-banger 303 algorithm")
    print(f"  Total rows: {NUM_ROWS}")
    print(f"  Steps per pattern: {TOTAL_STEPS} ({PHRASES_PER_CHAIN} x {STEPS_PER_PHRASE})")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Create Acid Banger 303 MIDI demo for M8 with external TB-03"
    )
    parser.add_argument(
        "--channel", "-c",
        type=int,
        default=1,
        choices=range(1, 17),
        metavar="1-16",
        help="MIDI channel for TB-03 (default: 1)"
    )
    parser.add_argument(
        "--off-prob", "-o",
        type=float,
        default=0.5,
        metavar="0.0-1.0",
        help="Probability of inserting OFF notes after each note (default: 0.5)"
    )
    args = parser.parse_args()

    # Validate off-prob range
    if not 0.0 <= args.off_prob <= 1.0:
        parser.error("--off-prob must be between 0.0 and 1.0")

    project = create_acid_banger_303_midi_project(args.channel, args.off_prob)
    save_project(project)


if __name__ == '__main__':
    main()
