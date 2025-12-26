#!/usr/bin/env python

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
- 120 phrases (0x00-0x77) split across 30 chains for triads
  - 10 rows × 12 phrases per row
  - Each row: 3 chains (root, 3rd, 5th) × 4 chords
- 30 chains (0x00-0x1D) - 3 per song row
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

# 10 famous EDM/electronic chord progressions
# Each progression has 4 chords split into root, 3rd, and 5th notes
CHORD_PROGRESSIONS = [
    # Row 0: Classic EDM (I-vi-IV-V in C major)
    {
        'name': 'Classic EDM',
        'song': 'Generic EDM progression',
        'chords': [
            {'name': 'C maj', 'root': M8Note.C_5, 'third': M8Note.E_5, 'fifth': M8Note.G_5},
            {'name': 'A min', 'root': M8Note.A_4, 'third': M8Note.C_5, 'fifth': M8Note.E_5},
            {'name': 'F maj', 'root': M8Note.F_4, 'third': M8Note.A_4, 'fifth': M8Note.C_5},
            {'name': 'G maj', 'root': M8Note.G_4, 'third': M8Note.B_4, 'fifth': M8Note.D_5},
        ],
        'pattern': [0, 4, 8, 12]  # Regular quarter notes
    },

    # Row 1: Kraftwerk - Computer World (vi-IV-I-V in C major)
    {
        'name': 'Computer World',
        'song': 'Kraftwerk - Computer World',
        'chords': [
            {'name': 'A min', 'root': M8Note.A_4, 'third': M8Note.C_5, 'fifth': M8Note.E_5},
            {'name': 'F maj', 'root': M8Note.F_4, 'third': M8Note.A_4, 'fifth': M8Note.C_5},
            {'name': 'C maj', 'root': M8Note.C_5, 'third': M8Note.E_5, 'fifth': M8Note.G_5},
            {'name': 'G maj', 'root': M8Note.G_4, 'third': M8Note.B_4, 'fifth': M8Note.D_5},
        ],
        'pattern': [0, 3, 6, 9, 12]  # Irregular timing
    },

    # Row 2: Daft Punk - Around The World (i-VII-VI-VII in A minor)
    {
        'name': 'Around The World',
        'song': 'Daft Punk - Around The World',
        'chords': [
            {'name': 'A min', 'root': M8Note.A_4, 'third': M8Note.C_5, 'fifth': M8Note.E_5},
            {'name': 'G maj', 'root': M8Note.G_4, 'third': M8Note.B_4, 'fifth': M8Note.D_5},
            {'name': 'F maj', 'root': M8Note.F_4, 'third': M8Note.A_4, 'fifth': M8Note.C_5},
            {'name': 'G maj', 'root': M8Note.G_4, 'third': M8Note.B_4, 'fifth': M8Note.D_5},
        ],
        'pattern': [0, 4, 8, 12]  # Regular
    },

    # Row 3: Deadmau5 - Strobe (vi-IV-I-V in E major, transposed)
    {
        'name': 'Strobe',
        'song': 'Deadmau5 - Strobe',
        'chords': [
            {'name': 'Cs min', 'root': M8Note.CS_5, 'third': M8Note.E_5, 'fifth': M8Note.GS_5},
            {'name': 'A maj', 'root': M8Note.A_4, 'third': M8Note.CS_5, 'fifth': M8Note.E_5},
            {'name': 'E maj', 'root': M8Note.E_5, 'third': M8Note.GS_5, 'fifth': M8Note.B_5},
            {'name': 'B maj', 'root': M8Note.B_4, 'third': M8Note.DS_5, 'fifth': M8Note.FS_5},
        ],
        'pattern': [0, 6, 10, 14]  # Irregular
    },

    # Row 4: Avicii - Levels (I-V-vi-IV in D major)
    {
        'name': 'Levels',
        'song': 'Avicii - Levels',
        'chords': [
            {'name': 'D maj', 'root': M8Note.D_5, 'third': M8Note.FS_5, 'fifth': M8Note.A_5},
            {'name': 'A maj', 'root': M8Note.A_4, 'third': M8Note.CS_5, 'fifth': M8Note.E_5},
            {'name': 'B min', 'root': M8Note.B_4, 'third': M8Note.D_5, 'fifth': M8Note.FS_5},
            {'name': 'G maj', 'root': M8Note.G_4, 'third': M8Note.B_4, 'fifth': M8Note.D_5},
        ],
        'pattern': [0, 4, 8, 12]  # Regular
    },

    # Row 5: The Prodigy - Breathe (i-VI-III-VII in E minor)
    {
        'name': 'Breathe',
        'song': 'The Prodigy - Breathe',
        'chords': [
            {'name': 'E min', 'root': M8Note.E_5, 'third': M8Note.G_5, 'fifth': M8Note.B_5},
            {'name': 'C maj', 'root': M8Note.C_5, 'third': M8Note.E_5, 'fifth': M8Note.G_5},
            {'name': 'G maj', 'root': M8Note.G_4, 'third': M8Note.B_4, 'fifth': M8Note.D_5},
            {'name': 'D maj', 'root': M8Note.D_5, 'third': M8Note.FS_5, 'fifth': M8Note.A_5},
        ],
        'pattern': [0, 2, 5, 8, 11, 14]  # Very irregular
    },

    # Row 6: Calvin Harris - Feel So Close (vi-IV-I-V in G major)
    {
        'name': 'Feel So Close',
        'song': 'Calvin Harris - Feel So Close',
        'chords': [
            {'name': 'E min', 'root': M8Note.E_5, 'third': M8Note.G_5, 'fifth': M8Note.B_5},
            {'name': 'C maj', 'root': M8Note.C_5, 'third': M8Note.E_5, 'fifth': M8Note.G_5},
            {'name': 'G maj', 'root': M8Note.G_4, 'third': M8Note.B_4, 'fifth': M8Note.D_5},
            {'name': 'D maj', 'root': M8Note.D_5, 'third': M8Note.FS_5, 'fifth': M8Note.A_5},
        ],
        'pattern': [0, 4, 8, 12]  # Regular
    },

    # Row 7: M83 - Midnight City (I-vi-iii-IV in Eb major)
    {
        'name': 'Midnight City',
        'song': 'M83 - Midnight City',
        'chords': [
            {'name': 'Eb maj', 'root': M8Note.DS_5, 'third': M8Note.G_5, 'fifth': M8Note.AS_5},
            {'name': 'C min', 'root': M8Note.C_5, 'third': M8Note.DS_5, 'fifth': M8Note.G_5},
            {'name': 'G min', 'root': M8Note.G_4, 'third': M8Note.AS_4, 'fifth': M8Note.D_5},
            {'name': 'Ab maj', 'root': M8Note.GS_4, 'third': M8Note.C_5, 'fifth': M8Note.DS_5},
        ],
        'pattern': [0, 3, 7, 11]  # Irregular
    },

    # Row 8: Justice - D.A.N.C.E. (I-V-vi-iii-IV-I-IV-V in C major)
    {
        'name': 'D.A.N.C.E.',
        'song': 'Justice - D.A.N.C.E.',
        'chords': [
            {'name': 'C maj', 'root': M8Note.C_5, 'third': M8Note.E_5, 'fifth': M8Note.G_5},
            {'name': 'G maj', 'root': M8Note.G_4, 'third': M8Note.B_4, 'fifth': M8Note.D_5},
            {'name': 'A min', 'root': M8Note.A_4, 'third': M8Note.C_5, 'fifth': M8Note.E_5},
            {'name': 'F maj', 'root': M8Note.F_4, 'third': M8Note.A_4, 'fifth': M8Note.C_5},
        ],
        'pattern': [0, 2, 4, 7, 9, 11, 13, 15]  # Complex timing
    },

    # Row 9: Röyksopp - Eple (i-VII-VI-V in A minor)
    {
        'name': 'Eple',
        'song': 'Röyksopp - Eple',
        'chords': [
            {'name': 'A min', 'root': M8Note.A_4, 'third': M8Note.C_5, 'fifth': M8Note.E_5},
            {'name': 'G maj', 'root': M8Note.G_4, 'third': M8Note.B_4, 'fifth': M8Note.D_5},
            {'name': 'F maj', 'root': M8Note.F_4, 'third': M8Note.A_4, 'fifth': M8Note.C_5},
            {'name': 'E maj', 'root': M8Note.E_5, 'third': M8Note.GS_5, 'fifth': M8Note.B_5},
        ],
        'pattern': [0, 5, 9, 13]  # Irregular
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


def create_single_note_phrase(note, velocity, pattern):
    """Create a phrase with a single note playing at specified steps.

    Args:
        note: The MIDI note to play
        velocity: Note velocity
        pattern: List of step positions where notes play

    Returns:
        M8Phrase with single note pattern
    """
    phrase = M8Phrase()

    for step in pattern:
        # Vary velocity slightly for dynamics
        step_velocity = velocity + random.randint(-8, 8)
        step_velocity = max(0x40, min(0x7F, step_velocity))  # Clamp to reasonable range

        phrase_step = M8PhraseStep(
            note=note,
            velocity=step_velocity,
            instrument=0x00  # Use instrument 0
        )

        # No FX - chords are created by parallel playback

        phrase[step] = phrase_step

    return phrase


def create_synth_chords_project():
    """Create the synth chords M8 project with 10 famous EDM progressions."""
    print(f"Creating Synth Chords demo: {PROJECT_NAME}")
    print(f"BPM: {BPM}, Seed: {SEED}")
    print(f"Creating 10 famous EDM chord progressions across 10 rows")
    print(f"Total: 30 chains (3 per row), 120 phrases (12 per row)")

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
        print(f"  Pattern: {progression['pattern']}")

        # Calculate base indices for this progression
        base_chain_idx = prog_idx * NUM_CHAINS  # 3 chains per progression
        base_phrase_idx = prog_idx * 12  # 12 phrases per progression (3 chains × 4 chords)

        # Create phrases for each voice (root, 3rd, 5th)
        for voice_idx in range(NUM_CHAINS):
            voice_name = voice_names[voice_idx]

            for chord_idx in range(4):
                chord = progression['chords'][chord_idx]
                phrase_idx = base_phrase_idx + (voice_idx * 4) + chord_idx

                # Get the note for this voice
                if voice_name == 'root':
                    note = chord['root']
                elif voice_name == 'third':
                    note = chord['third']
                else:  # fifth
                    note = chord['fifth']

                # Create phrase with single note and progression's pattern
                phrase = create_single_note_phrase(note, VELOCITIES[chord_idx], progression['pattern'])
                project.phrases[phrase_idx] = phrase

                print(f"  Phrase 0x{phrase_idx:02X}: {chord['name']} {voice_name} = {M8Note(note).name}")

        # Create 3 chains for this progression
        for voice_idx in range(NUM_CHAINS):
            chain_idx = base_chain_idx + voice_idx
            chain = M8Chain()

            for chord_idx in range(4):
                phrase_idx = base_phrase_idx + (voice_idx * 4) + chord_idx
                chain[chord_idx] = M8ChainStep(phrase=phrase_idx, transpose=0x00)

            project.chains[chain_idx] = chain

        # Add chains to song matrix row
        for voice_idx in range(NUM_CHAINS):
            chain_idx = base_chain_idx + voice_idx
            project.song[prog_idx][voice_idx] = chain_idx

        print(f"  Chains: 0x{base_chain_idx:02X}-0x{base_chain_idx+2:02X} at song row {prog_idx}")

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
    print(f"  Progressions: 10 famous EDM chord progressions")
    print(f"  Rendering: Polyphonic chords across 3 parallel tracks per row")
    print(f"  Total length: 10 rows × 64 steps = 640 steps (40 bars)")


def main():
    """Main entry point."""
    project = create_synth_chords_project()
    save_project(project)


if __name__ == '__main__':
    main()
