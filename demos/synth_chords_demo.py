#!/usr/bin/env python3

"""
Synth Chords Demo - 10 Famous EDM Chord Progressions using M8 Macrosynth

Demonstrates creating 10 famous electronic music chord progressions polyphonically
across multiple tracks. Includes progressions from:
- Kraftwerk (Computer World)
- Daft Punk (Around The World)
- Deadmau5 (Strobe)
- Avicii (Levels)
- The Prodigy (Breathe)
- Calvin Harris (Feel So Close)
- M83 (Midnight City)
- Justice (D.A.N.C.E.)
- Röyksopp (Eple)

Creates an M8 project with:
- 1 macrosynth instrument (0x00) with WTX4 shape (0x26) and volume envelope
- 30 phrases (0x00-0x1D) - 3 per song row (one per voice)
  - Each phrase contains all 4 chord changes with varied timing
- 30 chains (0x00-0x1D) - 3 per song row, each loops a single phrase
- Song arrangement: 10 rows with 3 chains each playing in parallel
- Various rhythmic patterns (regular and irregular)

Chords are rendered polyphonically with each voice on a separate chain.

Output: tmp/demos/synth_chords/SYNTH-CHORDS.m8s
"""

import random
from pathlib import Path

from m8.api.project import M8Project
from m8.api.instruments.macrosynth import M8Macrosynth, M8MacrosynthParam, M8MacroShape, M8MacrosynthModDest
from m8.api.phrase import M8Phrase, M8PhraseStep, M8Note
from m8.api.chain import M8Chain, M8ChainStep
from m8.api.fx import M8FXTuple, M8SequenceFX
from m8.api.modulator import M8Modulator, M8ModulatorType, M8AHDParam

# Configuration
PROJECT_NAME = "SYNTH-CHORDS"
OUTPUT_DIR = Path("tmp/demos/synth_chords")
BPM = 128
SEED = 42

# 10 famous EDM/electronic chord progressions with mid-phrase changes
# Each progression defines when each chord plays (step positions across 64 steps)
# Steps span 0-63 (4 phrases × 16 steps)
CHORD_PROGRESSIONS = [
    # Row 0: Orbital - Halcyon + On + On (syncopated changes)
    {
        'name': 'Halcyon',
        'song': 'Orbital - Halcyon + On + On',
        'chords': [
            {'name': 'D maj', 'root': M8Note.D_5, 'third': M8Note.FS_5, 'fifth': M8Note.A_5, 'steps': [0, 4, 16, 20, 32, 36, 48, 52]},
            {'name': 'Bm', 'root': M8Note.B_4, 'third': M8Note.D_5, 'fifth': M8Note.FS_5, 'steps': [8, 12, 24, 28, 40, 44, 56, 60]},
            {'name': 'G maj', 'root': M8Note.G_4, 'third': M8Note.B_4, 'fifth': M8Note.D_5, 'steps': [6, 22, 38, 54]},
            {'name': 'A maj', 'root': M8Note.A_4, 'third': M8Note.CS_5, 'fifth': M8Note.E_5, 'steps': [2, 10, 14, 18, 26, 30, 34, 42, 46, 50, 58, 62]},
        ],
    },

    # Row 1: Underworld - Born Slippy (fast, driving changes)
    {
        'name': 'Born Slippy',
        'song': 'Underworld - Born Slippy',
        'chords': [
            {'name': 'C maj', 'root': M8Note.C_5, 'third': M8Note.E_5, 'fifth': M8Note.G_5, 'steps': [0, 2, 16, 18, 32, 34, 48, 50]},
            {'name': 'Am', 'root': M8Note.A_4, 'third': M8Note.C_5, 'fifth': M8Note.E_5, 'steps': [4, 6, 20, 22, 36, 38, 52, 54]},
            {'name': 'F maj', 'root': M8Note.F_4, 'third': M8Note.A_4, 'fifth': M8Note.C_5, 'steps': [8, 24, 40, 56]},
            {'name': 'G maj', 'root': M8Note.G_4, 'third': M8Note.B_4, 'fifth': M8Note.D_5, 'steps': [10, 11, 12, 14, 26, 27, 28, 30, 42, 43, 44, 46, 58, 59, 60, 62]},
        ],
    },

    # Row 2: Chemical Brothers - Block Rockin' Beats (syncopated breaks)
    {
        'name': 'Block Rockin',
        'song': 'Chemical Brothers - Block Rockin\' Beats',
        'chords': [
            {'name': 'Em', 'root': M8Note.E_5, 'third': M8Note.G_5, 'fifth': M8Note.B_5, 'steps': [0, 3, 6, 16, 19, 22, 32, 35, 38, 48, 51, 54]},
            {'name': 'G maj', 'root': M8Note.G_4, 'third': M8Note.B_4, 'fifth': M8Note.D_5, 'steps': [8, 11, 24, 27, 40, 43, 56, 59]},
            {'name': 'D maj', 'root': M8Note.D_5, 'third': M8Note.FS_5, 'fifth': M8Note.A_5, 'steps': [13, 29, 45, 61]},
            {'name': 'Am', 'root': M8Note.A_4, 'third': M8Note.C_5, 'fifth': M8Note.E_5, 'steps': [15, 31, 47, 63]},
        ],
    },

    # Row 3: Boards of Canada - Roygbiv (irregular, nostalgic timing)
    {
        'name': 'Roygbiv',
        'song': 'Boards of Canada - Roygbiv',
        'chords': [
            {'name': 'F maj', 'root': M8Note.F_4, 'third': M8Note.A_4, 'fifth': M8Note.C_5, 'steps': [0, 1, 2, 5, 16, 17, 18, 21, 32, 33, 34, 37, 48, 49, 50, 53]},
            {'name': 'C maj', 'root': M8Note.C_5, 'third': M8Note.E_5, 'fifth': M8Note.G_5, 'steps': [7, 9, 23, 25, 39, 41, 55, 57]},
            {'name': 'Dm', 'root': M8Note.D_5, 'third': M8Note.F_5, 'fifth': M8Note.A_5, 'steps': [11, 27, 43, 59]},
            {'name': 'Bb maj', 'root': M8Note.AS_4, 'third': M8Note.D_5, 'fifth': M8Note.F_5, 'steps': [13, 14, 29, 30, 45, 46, 61, 62]},
        ],
    },

    # Row 4: LCD Soundsystem - Dance Yrself Clean (off-beat, building)
    {
        'name': 'Dance Clean',
        'song': 'LCD Soundsystem - Dance Yrself Clean',
        'chords': [
            {'name': 'Em', 'root': M8Note.E_5, 'third': M8Note.G_5, 'fifth': M8Note.B_5, 'steps': [0, 3, 16, 19, 32, 35, 48, 51]},
            {'name': 'C maj', 'root': M8Note.C_5, 'third': M8Note.E_5, 'fifth': M8Note.G_5, 'steps': [5, 7, 21, 23, 37, 39, 53, 55]},
            {'name': 'G maj', 'root': M8Note.G_4, 'third': M8Note.B_4, 'fifth': M8Note.D_5, 'steps': [9, 25, 41, 57]},
            {'name': 'D maj', 'root': M8Note.D_5, 'third': M8Note.FS_5, 'fifth': M8Note.A_5, 'steps': [12, 14, 15, 28, 30, 31, 44, 46, 47, 60, 62, 63]},
        ],
    },

    # Row 5: Daft Punk - Harder Better Faster Stronger (staccato, quick)
    {
        'name': 'Harder Better',
        'song': 'Daft Punk - Harder Better Faster Stronger',
        'chords': [
            {'name': 'Eb maj', 'root': M8Note.DS_5, 'third': M8Note.G_5, 'fifth': M8Note.AS_5, 'steps': [0, 2, 4, 16, 18, 20, 32, 34, 36, 48, 50, 52]},
            {'name': 'Cm', 'root': M8Note.C_5, 'third': M8Note.DS_5, 'fifth': M8Note.G_5, 'steps': [6, 22, 38, 54]},
            {'name': 'Ab maj', 'root': M8Note.GS_4, 'third': M8Note.C_5, 'fifth': M8Note.DS_5, 'steps': [8, 10, 24, 26, 40, 42, 56, 58]},
            {'name': 'Bb maj', 'root': M8Note.AS_4, 'third': M8Note.D_5, 'fifth': M8Note.F_5, 'steps': [11, 13, 15, 27, 29, 31, 43, 45, 47, 59, 61, 63]},
        ],
    },

    # Row 6: Porter Robinson - Sad Machine (emotional, complex)
    {
        'name': 'Sad Machine',
        'song': 'Porter Robinson - Sad Machine',
        'chords': [
            {'name': 'C maj', 'root': M8Note.C_5, 'third': M8Note.E_5, 'fifth': M8Note.G_5, 'steps': [0, 4, 16, 20, 32, 36, 48, 52]},
            {'name': 'Em', 'root': M8Note.E_5, 'third': M8Note.G_5, 'fifth': M8Note.B_5, 'steps': [6, 7, 22, 23, 38, 39, 54, 55]},
            {'name': 'Am', 'root': M8Note.A_4, 'third': M8Note.C_5, 'fifth': M8Note.E_5, 'steps': [9, 11, 25, 27, 41, 43, 57, 59]},
            {'name': 'F maj', 'root': M8Note.F_4, 'third': M8Note.A_4, 'fifth': M8Note.C_5, 'steps': [13, 14, 15, 29, 30, 31, 45, 46, 47, 61, 62, 63]},
        ],
    },

    # Row 7: Flume - Say It (modern, glitchy syncopation)
    {
        'name': 'Say It',
        'song': 'Flume - Say It',
        'chords': [
            {'name': 'Gb maj', 'root': M8Note.FS_4, 'third': M8Note.AS_4, 'fifth': M8Note.CS_5, 'steps': [0, 1, 3, 16, 17, 19, 32, 33, 35, 48, 49, 51]},
            {'name': 'Ebm', 'root': M8Note.DS_5, 'third': M8Note.FS_5, 'fifth': M8Note.AS_5, 'steps': [5, 8, 21, 24, 37, 40, 53, 56]},
            {'name': 'Db maj', 'root': M8Note.CS_5, 'third': M8Note.F_5, 'fifth': M8Note.GS_5, 'steps': [10, 26, 42, 58]},
            {'name': 'Ab maj', 'root': M8Note.GS_4, 'third': M8Note.C_5, 'fifth': M8Note.DS_5, 'steps': [12, 14, 28, 30, 44, 46, 60, 62]},
        ],
    },

    # Row 8: ODESZA - Say My Name (future bass, uplifting)
    {
        'name': 'Say My Name',
        'song': 'ODESZA - Say My Name',
        'chords': [
            {'name': 'F maj', 'root': M8Note.F_4, 'third': M8Note.A_4, 'fifth': M8Note.C_5, 'steps': [0, 2, 5, 16, 18, 21, 32, 34, 37, 48, 50, 53]},
            {'name': 'C maj', 'root': M8Note.C_5, 'third': M8Note.E_5, 'fifth': M8Note.G_5, 'steps': [7, 23, 39, 55]},
            {'name': 'Dm', 'root': M8Note.D_5, 'third': M8Note.F_5, 'fifth': M8Note.A_5, 'steps': [9, 11, 25, 27, 41, 43, 57, 59]},
            {'name': 'Bb maj', 'root': M8Note.AS_4, 'third': M8Note.D_5, 'fifth': M8Note.F_5, 'steps': [12, 13, 15, 28, 29, 31, 44, 45, 47, 60, 61, 63]},
        ],
    },

    # Row 9: Kraftwerk - Computer World (staccato, robotic, mechanical)
    {
        'name': 'Computer World',
        'song': 'Kraftwerk - Computer World',
        'chords': [
            {'name': 'Am', 'root': M8Note.A_4, 'third': M8Note.C_5, 'fifth': M8Note.E_5, 'steps': [0, 3, 5, 16, 19, 21, 32, 35, 37, 48, 51, 53]},
            {'name': 'F maj', 'root': M8Note.F_4, 'third': M8Note.A_4, 'fifth': M8Note.C_5, 'steps': [7, 23, 39, 55]},
            {'name': 'C maj', 'root': M8Note.C_5, 'third': M8Note.E_5, 'fifth': M8Note.G_5, 'steps': [9, 10, 25, 26, 41, 42, 57, 58]},
            {'name': 'G maj', 'root': M8Note.G_4, 'third': M8Note.B_4, 'fifth': M8Note.D_5, 'steps': [12, 15, 28, 31, 44, 47, 60, 63]},
        ],
    },
]

# Number of chains (one per chord voice)
NUM_CHAINS = 3  # Root, 3rd, 5th

# Velocities for variation (creating dynamics)
VELOCITIES = [
    0x5F,  # Medium-soft
    0x6F,  # Medium
    0x7F,  # Medium-loud
    0x6F,  # Medium
]


def create_macrosynth_instrument():
    """Create a macrosynth instrument with WTX4 shape and volume envelope.

    Returns:
        M8Macrosynth configured for chord playing
    """
    # Create macrosynth with basic settings
    macrosynth = M8Macrosynth(name="CHORDS")

    # Set shape to 0x26 (WTX4 - Wavetable 4X)
    macrosynth.set(M8MacrosynthParam.SHAPE, 0x26)
    macrosynth.set(M8MacrosynthParam.VOLUME, 0x00)
    macrosynth.set(M8MacrosynthParam.PITCH, 0x00)
    macrosynth.set(M8MacrosynthParam.FINE_TUNE, 0x80)  # Center
    macrosynth.set(M8MacrosynthParam.PAN, 0x80)  # Center pan

    # Timbre and colour (synthesis parameters)
    macrosynth.set(M8MacrosynthParam.TIMBRE, 0x80)  # Center
    macrosynth.set(M8MacrosynthParam.COLOUR, 0x80)  # Center

    # Effects sends - only chorus enabled
    macrosynth.set(M8MacrosynthParam.CHORUS_SEND, 0xC0)  # Chorus to 0xC0
    macrosynth.set(M8MacrosynthParam.DELAY_SEND, 0x00)   # Delay off
    macrosynth.set(M8MacrosynthParam.REVERB_SEND, 0x00)  # Reverb off

    # Filter off
    macrosynth.set(M8MacrosynthParam.FILTER_TYPE, 0x00)  # Filter off
    macrosynth.set(M8MacrosynthParam.CUTOFF, 0xFF)       # Cutoff fully open
    macrosynth.set(M8MacrosynthParam.RESONANCE, 0x00)    # No resonance

    # Limiter off
    macrosynth.set(M8MacrosynthParam.LIMIT, 0x00)        # Limiter off
    macrosynth.set(M8MacrosynthParam.AMP, 0x00)          # Amp at default

    # Create AHD envelope for volume (first modulator only)
    mod_volume = macrosynth.modulators[0]
    mod_volume.mod_type = M8ModulatorType.AHD_ENVELOPE
    mod_volume.destination = M8MacrosynthModDest.VOLUME  # Use enum instead of integer
    mod_volume.amount = 0xFF  # Full amount

    # Set AHD envelope parameters using the enum offsets
    mod_volume.set(M8AHDParam.ATTACK, 0x00)  # Attack: 0
    mod_volume.set(M8AHDParam.HOLD, 0x00)    # Hold: 0
    mod_volume.set(M8AHDParam.DECAY, 0x80)   # Decay: medium

    # Turn off other modulators (set destination to OFF)
    for i in range(1, 4):
        macrosynth.modulators[i].destination = M8MacrosynthModDest.OFF

    return macrosynth


def create_multi_chord_phrase(chords, voice_name, phrase_idx, start_step, end_step):
    """Create a phrase with multiple chords playing at different steps.

    Args:
        chords: List of chord dicts with 'root', 'third', 'fifth', and 'steps' keys
        voice_name: Which voice to extract ('root', 'third', or 'fifth')
        phrase_idx: Phrase index (0-3) for velocity variation
        start_step: Starting global step for this phrase (e.g., 0, 16, 32, 48)
        end_step: Ending global step for this phrase (exclusive)

    Returns:
        M8Phrase with multiple chord changes
    """
    phrase = M8Phrase()

    # Iterate through all chords and place notes if their steps fall in this phrase's range
    for chord_idx, chord in enumerate(chords):
        # Get the note for this voice
        note = chord[voice_name]

        # Get base velocity for this chord (varies per chord)
        base_velocity = VELOCITIES[chord_idx]

        # Check which of this chord's steps fall within this phrase's range
        for global_step in chord['steps']:
            if start_step <= global_step < end_step:
                # Calculate local step position within the phrase (0-15)
                local_step = global_step - start_step

                # Vary velocity slightly for dynamics
                step_velocity = base_velocity + random.randint(-8, 8)
                step_velocity = max(0x40, min(0x7F, step_velocity))  # Clamp to reasonable range

                phrase_step = M8PhraseStep(
                    note=note,
                    velocity=step_velocity,
                    instrument=0x00  # Use instrument 0
                )

                phrase[local_step] = phrase_step

    return phrase


def create_synth_chords_project():
    """Create the synth chords M8 project with 10 famous EDM progressions."""
    print(f"Creating Synth Chords demo: {PROJECT_NAME}")
    print(f"BPM: {BPM}, Seed: {SEED}")
    print(f"Creating 10 famous EDM chord progressions across 10 rows")
    print(f"Total: 30 chains (3 per row), 120 phrases (12 per row)")
    print(f"Each row: 64 steps (4 phrases × 16 steps) with chord changes mid-phrase")

    # Initialize project
    project = M8Project.initialise()
    project.metadata.name = PROJECT_NAME
    project.metadata.tempo = BPM
    project.metadata.directory = "/Songs/pym8-demos/synth-chords/"

    # Create macrosynth instrument
    macrosynth = create_macrosynth_instrument()
    project.instruments[0x00] = macrosynth
    print(f"\nInstrument 0x00: CHORDS (shape=WTX4/0x26)")
    print(f"  Modulator 0: AHD_ENVELOPE -> VOLUME (others OFF)")
    print(f"  Filter: OFF, Limiter: OFF")
    print(f"  Effects: Chorus=0xC0, Delay=OFF, Reverb=OFF")

    voice_names = ['root', 'third', 'fifth']

    # Create phrases and chains for all 10 progressions
    for prog_idx, progression in enumerate(CHORD_PROGRESSIONS):
        print(f"\n{'='*60}")
        print(f"Row {prog_idx}: {progression['name']}")
        print(f"  Song: {progression['song']}")

        # Calculate base indices for this progression
        base_chain_idx = prog_idx * NUM_CHAINS  # 3 chains per progression
        base_phrase_idx = prog_idx * 12  # 12 phrases per progression (3 voices × 4 phrases)

        # Create phrases for each voice (root, 3rd, 5th)
        for voice_idx in range(NUM_CHAINS):
            voice_name = voice_names[voice_idx]

            # Create 4 phrases for this voice (16 steps each = 64 total)
            for phrase_num in range(4):
                phrase_idx = base_phrase_idx + (voice_idx * 4) + phrase_num

                # Calculate step range for this phrase
                start_step = phrase_num * 16  # 0, 16, 32, 48
                end_step = start_step + 16    # 16, 32, 48, 64

                # Create phrase with multiple chord changes
                phrase = create_multi_chord_phrase(
                    progression['chords'],
                    voice_name,
                    phrase_num,
                    start_step,
                    end_step
                )
                project.phrases[phrase_idx] = phrase

                # Count how many notes are in this phrase (skip empty steps)
                note_count = sum(1 for step in phrase if step.note != 255)
                print(f"  Phrase 0x{phrase_idx:02X}: {voice_name} steps {start_step}-{end_step-1} ({note_count} notes)")

        # Create 3 chains for this progression (one per voice)
        for voice_idx in range(NUM_CHAINS):
            chain_idx = base_chain_idx + voice_idx
            chain = M8Chain()

            # Each chain has 4 steps, pointing to the 4 phrases for this voice
            for phrase_num in range(4):
                phrase_idx = base_phrase_idx + (voice_idx * 4) + phrase_num
                chain[phrase_num] = M8ChainStep(phrase=phrase_idx, transpose=0x00)

            project.chains[chain_idx] = chain

        # Add chains to song matrix row
        for voice_idx in range(NUM_CHAINS):
            chain_idx = base_chain_idx + voice_idx
            project.song[prog_idx][voice_idx] = chain_idx

        print(f"  Chains: 0x{base_chain_idx:02X}-0x{base_chain_idx+2:02X} at song row {prog_idx}, 64 steps total")

    print(f"\n{'='*60}")
    print(f"Song arrangement: 10 rows × 3 chains (polyphonic chords)")

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
    print(f"  Structure: 1 instrument, 120 phrases, 30 chains, 10 song rows")
    print(f"  Progressions: 10 famous EDM chord progressions with mid-phrase changes")
    print(f"  Rendering: Polyphonic chords across 3 parallel tracks per row")
    print(f"  Pattern style: Each row has 64 steps (4×16) with syncopated chord changes")
    print(f"  Total length: 10 rows × 64 steps = 640 steps (40 bars)")


def main():
    """Main entry point."""
    project = create_synth_chords_project()
    save_project(project)


if __name__ == '__main__':
    main()
