#!/usr/bin/env python

"""
Synth Chords Demo - EDM chord progression using M8 Macrosynth

Demonstrates creating chord progressions polyphonically across multiple tracks.
Uses a classic EDM chord progression: C major - A minor - F major - G major
(I - vi - IV - V in C major scale)

Creates an M8 project with:
- 1 macrosynth instrument (0x00) with WTX4 shape (0x26) and volume envelope
- 12 phrases (0x00-0x0B) split across 3 chains for triads
  - Chain 0 (phrases 00-03): root notes
  - Chain 1 (phrases 04-07): 3rd notes
  - Chain 2 (phrases 08-0B): 5th notes
- 3 chains (0x00-0x02) placed in first row of song matrix
- Song arrangement: chains at [0,0], [0,1], [0,2] play in parallel
- All notes shifted up one octave

Chords are rendered polyphonically:
- Phrases 00, 04, 08 play together = C major (C5-E5-G5)
- Phrases 01, 05, 09 play together = A minor (A4-C5-E5)
- Phrases 02, 06, 0A play together = F major (F4-A4-C5)
- Phrases 03, 07, 0B play together = G major (G4-B4-D5)

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

# Chord progression: C major - A minor - F major - G major (I - vi - IV - V)
# Each chord is split into root, 3rd, and 5th notes
# All notes shifted up one octave
CHORDS = [
    # C major: C-E-G
    {
        'name': 'C major',
        'root': M8Note.C_5,
        'third': M8Note.E_5,
        'fifth': M8Note.G_5,
    },
    # A minor: A-C-E
    {
        'name': 'A minor',
        'root': M8Note.A_4,
        'third': M8Note.C_5,
        'fifth': M8Note.E_5,
    },
    # F major: F-A-C
    {
        'name': 'F major',
        'root': M8Note.F_4,
        'third': M8Note.A_4,
        'fifth': M8Note.C_5,
    },
    # G major: G-B-D
    {
        'name': 'G major',
        'root': M8Note.G_4,
        'third': M8Note.B_4,
        'fifth': M8Note.D_5,
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


def create_single_note_phrase(note, velocity):
    """Create a phrase with a single note playing on quarter notes.

    Args:
        note: The MIDI note to play
        velocity: Note velocity

    Returns:
        M8Phrase with single note pattern
    """
    phrase = M8Phrase()

    # Create pattern - play on steps 0, 4, 8, 12 (quarter notes)
    chord_steps = [0, 4, 8, 12]

    for step in chord_steps:
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
    """Create the synth chords M8 project."""
    print(f"Creating Synth Chords demo: {PROJECT_NAME}")
    print(f"BPM: {BPM}, Seed: {SEED}")
    print(f"Chord progression: C major - A minor - F major - G major (I-vi-IV-V)")
    print(f"Rendering chords polyphonically across {NUM_CHAINS} parallel tracks")

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

    # Create 12 phrases (3 chains × 4 chords)
    # Chain 0: phrases 00-03 (root notes)
    # Chain 1: phrases 04-07 (3rd notes)
    # Chain 2: phrases 08-0B (5th notes)

    voice_names = ['root', 'third', 'fifth']

    for chain_idx in range(NUM_CHAINS):
        voice_name = voice_names[chain_idx]
        print(f"\nChain {chain_idx} - {voice_name} notes:")

        for chord_idx in range(4):
            chord = CHORDS[chord_idx]
            phrase_idx = chain_idx * 4 + chord_idx

            # Get the note for this voice
            if voice_name == 'root':
                note = chord['root']
            elif voice_name == 'third':
                note = chord['third']
            else:  # fifth
                note = chord['fifth']

            # Create phrase with single note
            phrase = create_single_note_phrase(note, VELOCITIES[chord_idx])
            project.phrases[phrase_idx] = phrase

            print(f"  Phrase 0x{phrase_idx:02X}: {chord['name']} {voice_name} = {M8Note(note).name}")

    # Create 3 chains, each containing 4 phrases
    for chain_idx in range(NUM_CHAINS):
        chain = M8Chain()
        for phrase_offset in range(4):
            phrase_idx = chain_idx * 4 + phrase_offset
            chain[phrase_offset] = M8ChainStep(phrase=phrase_idx, transpose=0x00)
        project.chains[chain_idx] = chain

        phrase_range = f"0x{chain_idx * 4:02X}-0x{chain_idx * 4 + 3:02X}"
        print(f"\nChain 0x{chain_idx:02X}: phrases {phrase_range}")

    # Add all 3 chains to first row of song matrix (parallel playback)
    for chain_idx in range(NUM_CHAINS):
        project.song[0][chain_idx] = chain_idx

    print(f"\nSong arrangement:")
    print(f"  Row 0: Chains 0x00, 0x01, 0x02 (playing in parallel)")
    print(f"  Chords rendered polyphonically:")
    print(f"    Phrases 00+04+08 = C major (C-E-G)")
    print(f"    Phrases 01+05+09 = A minor (A-C-E)")
    print(f"    Phrases 02+06+0A = F major (F-A-C)")
    print(f"    Phrases 03+07+0B = G major (G-B-D)")

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
    print(f"  Structure: 1 instrument, 12 phrases, 3 chains")
    print(f"  Progression: C major - A minor - F major - G major (I-vi-IV-V)")
    print(f"  Rendering: Polyphonic chords across 3 parallel tracks")
    print(f"  Total length: 64 steps (4 bars)")


def main():
    """Main entry point."""
    project = create_synth_chords_project()
    save_project(project)


if __name__ == '__main__':
    main()
