#!/usr/bin/env python

"""
Synth Chords Demo - EDM chord progression using M8 Wavsynth

Demonstrates creating chord progressions polyphonically across multiple tracks.
Uses a classic EDM chord progression: C major - A minor - F major - G major
(I - vi - IV - V in C major scale)

Creates an M8 project with:
- 1 wavsynth instrument (0x00) with random shape and volume envelope
- 12 phrases (0x00-0x0B) split across 3 chains for triads
  - Chain 0 (phrases 00-03): root notes
  - Chain 1 (phrases 04-07): 3rd notes
  - Chain 2 (phrases 08-0B): 5th notes
- 3 chains (0x00-0x02) placed in first row of song matrix
- Song arrangement: chains at [0,0], [0,1], [0,2] play in parallel

Chords are rendered polyphonically:
- Phrases 00, 04, 08 play together = C major (C-E-G)
- Phrases 01, 05, 09 play together = A minor (A-C-E)
- Phrases 02, 06, 0A play together = F major (F-A-C)
- Phrases 03, 07, 0B play together = G major (G-B-D)

Output: tmp/demos/synth_chords/SYNTH-CHORDS.m8s
"""

import random
from pathlib import Path

from m8.api.project import M8Project
from m8.api.instruments.wavsynth import M8Wavsynth, M8WavsynthParam, M8WavShape, M8WavsynthModDest
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
CHORDS = [
    # C major: C-E-G
    {
        'name': 'C major',
        'root': M8Note.C_4,
        'third': M8Note.E_4,
        'fifth': M8Note.G_4,
    },
    # A minor: A-C-E
    {
        'name': 'A minor',
        'root': M8Note.A_3,
        'third': M8Note.C_4,
        'fifth': M8Note.E_4,
    },
    # F major: F-A-C
    {
        'name': 'F major',
        'root': M8Note.F_3,
        'third': M8Note.A_3,
        'fifth': M8Note.C_4,
    },
    # G major: G-B-D
    {
        'name': 'G major',
        'root': M8Note.G_3,
        'third': M8Note.B_3,
        'fifth': M8Note.D_4,
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


def create_wavsynth_instrument(rng):
    """Create a wavsynth instrument with random shape and volume envelope.

    Args:
        rng: Random number generator

    Returns:
        M8Wavsynth configured for chord playing
    """
    # Choose random wave shape
    wave_shapes = [
        M8WavShape.PULSE12, M8WavShape.PULSE25, M8WavShape.PULSE50,
        M8WavShape.SAW, M8WavShape.TRIANGLE, M8WavShape.SINE,
        M8WavShape.WT_CRUSH, M8WavShape.WT_FOLDING, M8WavShape.WT_LIQUID,
    ]
    chosen_shape = rng.choice(wave_shapes)

    # Create wavsynth with basic settings
    wavsynth = M8Wavsynth(name="CHORDS")

    # Set basic parameters
    wavsynth.set(M8WavsynthParam.SHAPE, chosen_shape)
    wavsynth.set(M8WavsynthParam.VOLUME, 0x00)
    wavsynth.set(M8WavsynthParam.PITCH, 0x00)
    wavsynth.set(M8WavsynthParam.FINE_TUNE, 0x80)  # Center
    wavsynth.set(M8WavsynthParam.PAN, 0x80)  # Center pan
    wavsynth.set(M8WavsynthParam.CHORUS_SEND, 0xC0)  # Set chorus to 0xC0
    wavsynth.set(M8WavsynthParam.DELAY_SEND, 0x40)
    wavsynth.set(M8WavsynthParam.REVERB_SEND, 0x60)

    # Create AHD envelope for volume (first modulator)
    # Using the default modulator and just changing the destination to VOLUME
    mod_volume = wavsynth.modulators[0]
    mod_volume.mod_type = M8ModulatorType.AHD_ENVELOPE
    mod_volume.destination = M8WavsynthModDest.VOLUME  # Use enum instead of integer
    mod_volume.amount = 0xFF  # Full amount

    # Set AHD envelope parameters using the enum offsets
    mod_volume.set(M8AHDParam.ATTACK, 0x00)  # Attack: 0
    mod_volume.set(M8AHDParam.HOLD, 0x00)    # Hold: 0
    mod_volume.set(M8AHDParam.DECAY, 0x80)   # Decay: medium

    return wavsynth, chosen_shape


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

    # Initialize RNG with seed for reproducible results
    rng = random.Random(SEED)

    # Initialize project
    project = M8Project.initialise()
    project.metadata.name = PROJECT_NAME
    project.metadata.tempo = BPM
    project.metadata.directory = "/Songs/pym8-demos/synth-chords/"

    # Create wavsynth instrument
    wavsynth, chosen_shape = create_wavsynth_instrument(rng)
    project.instruments[0x00] = wavsynth
    print(f"\nInstrument 0x00: CHORDS (shape={M8WavShape(chosen_shape).name})")
    print(f"  Modulator 0: AHD_ENVELOPE -> VOLUME")
    print(f"  Chorus send: 0xC0")

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
