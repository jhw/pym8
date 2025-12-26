#!/usr/bin/env python

"""
Synth Chords Demo - EDM chord progression using M8 Wavsynth

Demonstrates creating chord progressions using the ARP (arpeggio) FX command.
Uses a classic EDM chord progression: C major - A minor - F major - G major
(I - vi - IV - V in C major scale)

Creates an M8 project with:
- 1 wavsynth instrument (0x00) with random shape and volume envelope
- 4 phrases (0x00-0x03) containing the chord progression
- 1 chain (0x00) referencing all 4 phrases
- Song arrangement: chain 0x00 at position [0,0] (top-left)

Each chord uses the ARP FX command with values:
- Major chord: 0x47 (+4 and +7 semitones for major 3rd and perfect 5th)
- Minor chord: 0x37 (+3 and +7 semitones for minor 3rd and perfect 5th)

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
# Root notes for each phrase
CHORD_ROOTS = [
    M8Note.C_4,   # Phrase 0: C major
    M8Note.A_3,   # Phrase 1: A minor
    M8Note.F_3,   # Phrase 2: F major
    M8Note.G_3,   # Phrase 3: G major
]

# ARP FX values for chord types
ARP_MAJOR = 0x47  # +4 and +7 semitones (major 3rd and perfect 5th)
ARP_MINOR = 0x37  # +3 and +7 semitones (minor 3rd and perfect 5th)

# Chord types for each phrase (True = major, False = minor)
CHORD_TYPES = [
    True,   # C major
    False,  # A minor
    True,   # F major
    True,   # G major
]

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


def create_chord_phrase(phrase_idx, root_note, is_major, velocity):
    """Create a phrase with chord progression using ARP FX.

    Args:
        phrase_idx: Index of the phrase (0-3)
        root_note: Root note of the chord
        is_major: True for major chord, False for minor
        velocity: Note velocity

    Returns:
        M8Phrase with chord pattern
    """
    phrase = M8Phrase()
    arp_value = ARP_MAJOR if is_major else ARP_MINOR

    # Create chord pattern - play on steps 0, 4, 8, 12 (quarter notes)
    chord_steps = [0, 4, 8, 12]

    for step in chord_steps:
        # Vary velocity slightly for dynamics
        step_velocity = velocity + random.randint(-8, 8)
        step_velocity = max(0x40, min(0x7F, step_velocity))  # Clamp to reasonable range

        phrase_step = M8PhraseStep(
            note=root_note,
            velocity=step_velocity,
            instrument=0x00  # Use instrument 0
        )

        # Add arpeggio FX to create the chord
        phrase_step.fx[0] = M8FXTuple(key=M8SequenceFX.ARP, value=arp_value)

        phrase[step] = phrase_step

    return phrase


def create_synth_chords_project():
    """Create the synth chords M8 project."""
    print(f"Creating Synth Chords demo: {PROJECT_NAME}")
    print(f"BPM: {BPM}, Seed: {SEED}")
    print(f"Chord progression: C major - A minor - F major - G major (I-vi-IV-V)")

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

    # Create 4 phrases with chord progression
    chord_names = ["C major", "A minor", "F major", "G major"]
    for i in range(4):
        phrase = create_chord_phrase(
            phrase_idx=i,
            root_note=CHORD_ROOTS[i],
            is_major=CHORD_TYPES[i],
            velocity=VELOCITIES[i]
        )
        project.phrases[i] = phrase

        arp_type = "major (0x47)" if CHORD_TYPES[i] else "minor (0x37)"
        print(f"\nPhrase 0x{i:02X}: {chord_names[i]} - root={M8Note(CHORD_ROOTS[i]).name}")
        print(f"  ARP FX: {arp_type}")
        print(f"  Pattern: quarter notes on steps 0, 4, 8, 12")

    # Create chain referencing all 4 phrases
    chain = M8Chain()
    for i in range(4):
        chain[i] = M8ChainStep(phrase=i, transpose=0x00)
    project.chains[0x00] = chain
    print(f"\nChain 0x00: phrases 0x00-0x03 (64 steps total)")

    # Add chain to song matrix at top-left position [0,0]
    project.song[0][0] = 0x00
    print(f"\nSong arrangement: Chain 0x00 at position [row=0, track=0] (top-left)")

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
    print(f"  Structure: 1 instrument, 4 phrases, 1 chain")
    print(f"  Progression: C major - A minor - F major - G major (I-vi-IV-V)")
    print(f"  Total length: 64 steps (4 bars)")


def main():
    """Main entry point."""
    project = create_synth_chords_project()
    save_project(project)


if __name__ == '__main__':
    main()
