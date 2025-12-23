#!/usr/bin/env python

"""
Sampler Demo - A simple demonstration of creating an M8 project with a sampler instrument.

This demo creates:
- A sampler instrument with a sample from the Erica Pico default pack
- A phrase with random beats
- A chain that references the phrase
- A song row that references the chain
- Saves the project to tmp/demos/sampler_demo/SAMPLER-DEMO.m8s

The sample is copied to the samples/ subdirectory following M8 convention.
"""

import random
import shutil
from pathlib import Path

from m8.api.project import M8Project
from m8.api.sampler import M8Sampler, M8SamplerParam
from m8.api.phrase import M8Phrase, M8PhraseStep
from m8.api.chain import M8Chain, M8ChainStep
from m8.api.fx import M8FXTuple, M8SequenceFX, M8SamplerFX


# Configuration
DEMO_NAME = "SAMPLER-DEMO"
OUTPUT_DIR = Path("tmp/demos/sampler_demo")
SAMPLE_SOURCE_DIR = Path("/Users/jhw/work/gists/music/6014d1500bd8089900b63af39e6d7d8d/tmp/samples/erica-pico/default")
SAMPLE_FILENAME = "04BuchlaBD.wav"  # A nice kick drum sample
BPM = 120


def create_demo():
    """Create a simple M8 project demonstrating sampler usage"""

    print(f"Creating sampler demo project: {DEMO_NAME}")
    print(f"BPM: {BPM}")

    # Initialize project from template
    project = M8Project.initialise()
    project.metadata.name = DEMO_NAME
    project.metadata.tempo = BPM
    project.metadata.directory = "/Songs/pym8-demos/sampler_demo/"

    # Create sampler instrument
    # Reference is relative to the .m8s file location
    sampler = M8Sampler(
        name="KICK",
        sample_path=f"samples/{SAMPLE_FILENAME}"
    )

    # Set delay send on the instrument
    sampler.set(M8SamplerParam.DELAY_SEND, 0x80)

    # Add sampler to instrument slot 0
    project.instruments[0] = sampler
    print(f"Created sampler instrument 'KICK' -> samples/{SAMPLE_FILENAME}")
    print(f"Set instrument delay send to 0x80")

    # Create a phrase with random beats
    # M8 phrases have 16 steps
    phrase = M8Phrase()

    # FX codes - now using enums instead of raw hex values

    # Use seed for reproducibility
    random.seed(42)

    # Create beats with 50% probability and random FX
    print("Creating phrase with 16 steps (50% beat probability):")

    beat_count = 0
    for pos in range(16):
        # 50% chance of having a beat on this step
        if random.random() < 0.5:
            # Vary velocity across the range
            # Make every 4th step louder (downbeats)
            if pos % 4 == 0:
                velocity = random.randint(0x68, 0x6F)  # Louder
            else:
                velocity = random.randint(0x50, 0x65)  # Softer

            step = M8PhraseStep(
                note=0x24,  # C-4 (default middle C on M8)
                velocity=velocity,
                instrument=0x00  # Use instrument slot 0
            )

            # Choose FX randomly: 1 in 4 chance each for none/reverse/retrigger/cut
            fx_choice = random.randint(0, 3)
            fx_applied = []

            if fx_choice == 1:
                # Reverse play
                step.fx[0] = M8FXTuple(key=M8SamplerFX.PLY, value=0x01)
                fx_applied.append("PLY:REV")
            elif fx_choice == 2:
                # Retrigger
                step.fx[0] = M8FXTuple(key=M8SequenceFX.RET, value=0x40)
                fx_applied.append("RET:40")
            elif fx_choice == 3:
                # Length cut
                step.fx[0] = M8FXTuple(key=M8SamplerFX.LEN, value=0xC0)
                fx_applied.append("LEN:C0")
            # else: fx_choice == 0, no FX

            phrase[pos] = step
            beat_count += 1

            # Print step info
            fx_str = f" FX:[{','.join(fx_applied)}]" if fx_applied else ""
            print(f"  Step {pos:2d}: vel=0x{velocity:02X}{fx_str}")
        else:
            # No beat on this step
            print(f"  Step {pos:2d}: ---")

    # Add phrase to project at phrase slot 0
    project.phrases[0] = phrase
    print(f"\nPhrase created with {beat_count} beats (out of 16 steps)")

    # Create a chain with this phrase
    chain = M8Chain()
    chain_step = M8ChainStep(
        phrase=0x00,  # Reference phrase slot 0
        transpose=0x00
    )
    chain[0] = chain_step  # Set first step in chain

    # Add chain to project at chain slot 0
    project.chains[0] = chain
    print("Created chain referencing phrase 0")

    # Add chain to song matrix at row 0, column 0
    project.song[0][0] = 0x00  # Reference chain slot 0
    print("Added chain to song matrix at row 0, column 0")

    return project


def save_demo(project):
    """Save the demo project and copy the sample file"""

    # Create output directories
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    samples_dir = OUTPUT_DIR / "samples"
    samples_dir.mkdir(exist_ok=True)

    # Write M8 project file
    output_path = OUTPUT_DIR / f"{DEMO_NAME}.m8s"
    print(f"\nSaving project to {output_path}...")
    project.write_to_file(str(output_path))

    # Copy sample to samples directory
    sample_source = SAMPLE_SOURCE_DIR / SAMPLE_FILENAME
    sample_dest = samples_dir / SAMPLE_FILENAME

    if sample_source.exists():
        print(f"Copying sample {SAMPLE_FILENAME} to {samples_dir}...")
        shutil.copy2(sample_source, sample_dest)
    else:
        print(f"Warning: Sample source not found: {sample_source}")
        print("You'll need to provide your own sample file.")

    print(f"\n✓ Demo complete!")
    print(f"  Project: {output_path}")
    print(f"  Sample: {sample_dest}")
    print(f"\nYou can now copy this to your M8 device using:")
    print(f"  python tools/copy_demos_to_m8.py")


def main():
    """Main entry point"""
    project = create_demo()
    save_demo(project)


if __name__ == '__main__':
    main()
