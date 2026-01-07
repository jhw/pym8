#!/usr/bin/env python3

"""
External Instrument Test Demo - Verification of External instrument parameter offsets

Creates a single External instrument with randomly selected but sensible parameter
values across ALL parameters (not just defaults). This allows verification that
all parameter offsets are correctly mapped by loading the file on an M8 device
and checking each value matches.

Creates an M8 project with:
- 1 External instrument in slot 0x00 with randomized parameters
- 1 phrase (0x00) with a C-4 note on step 0, instrument 0x00
- 1 chain (0x00) referencing phrase 0x00
- Song with chain 0x00 at row 0, track 0

Output: tmp/demos/external_test/EXTERNAL-TEST.m8s
"""

import random
from pathlib import Path

from m8.api.project import M8Project
from m8.api.instruments.external import (
    M8External, M8ExternalParam, M8ExternalInput, M8ExternalPort
)
from m8.api.instrument import M8FilterType, M8LimiterType
from m8.api.phrase import M8Phrase, M8PhraseStep, M8Note
from m8.api.chain import M8Chain, M8ChainStep

# Configuration
PROJECT_NAME = "EXTERNAL-TEST"
OUTPUT_DIR = Path("tmp/demos/external_test")
BPM = 120
SEED = 12345


def create_test_external_instrument(rng):
    """Create an External instrument with random but sensible parameter values.

    Args:
        rng: Random number generator

    Returns:
        M8External instrument with randomized parameters
    """
    external = M8External(name="EXT-TEST")

    # Note: Common synth params (TRANSPOSE, TABLE_TICK, VOLUME, PITCH, FINE_TUNE)
    # exist in the binary but are not displayed for External instruments.
    # We leave them at defaults and don't set/report them.

    # MIDI parameters (all 0-127 range, displayed as decimal on device)
    input_val = rng.choice(list(M8ExternalInput))
    port_val = rng.choice(list(M8ExternalPort))
    channel = rng.randint(1, 16)  # MIDI channels 1-16
    bank = rng.randint(0, 127)
    program = rng.randint(0, 127)

    external.set(M8ExternalParam.INPUT, input_val)
    external.set(M8ExternalParam.PORT, port_val)
    external.set(M8ExternalParam.CHANNEL, channel)
    external.set(M8ExternalParam.BANK, bank)
    external.set(M8ExternalParam.PROGRAM, program)

    # CC parameters (4 slots, each with CC number 0-127 and value 0-127)
    # Using distinct CC numbers for easy identification
    cca_num, cca_val = rng.randint(1, 31), rng.randint(0, 127)
    ccb_num, ccb_val = rng.randint(32, 63), rng.randint(0, 127)
    ccc_num, ccc_val = rng.randint(64, 95), rng.randint(0, 127)
    ccd_num, ccd_val = rng.randint(96, 119), rng.randint(0, 127)

    external.set(M8ExternalParam.CCA_NUM, cca_num)
    external.set(M8ExternalParam.CCA_VAL, cca_val)
    external.set(M8ExternalParam.CCB_NUM, ccb_num)
    external.set(M8ExternalParam.CCB_VAL, ccb_val)
    external.set(M8ExternalParam.CCC_NUM, ccc_num)
    external.set(M8ExternalParam.CCC_VAL, ccc_val)
    external.set(M8ExternalParam.CCD_NUM, ccd_num)
    external.set(M8ExternalParam.CCD_VAL, ccd_val)

    # Filter parameters
    filter_type = rng.choice(list(M8FilterType))
    cutoff = rng.randint(0x20, 0xE0)  # Avoid extremes for visibility
    resonance = rng.randint(0x20, 0xC0)

    external.set(M8ExternalParam.FILTER_TYPE, filter_type)
    external.set(M8ExternalParam.CUTOFF, cutoff)
    external.set(M8ExternalParam.RESONANCE, resonance)

    # Mixer parameters
    amp = rng.randint(0x10, 0x40)
    limit = rng.choice(list(M8LimiterType))
    pan = rng.randint(0x40, 0xC0)  # Around center
    dry = rng.randint(0x80, 0xFF)
    chorus = rng.randint(0x00, 0x80)
    delay = rng.randint(0x00, 0x80)
    reverb = rng.randint(0x00, 0x80)

    external.set(M8ExternalParam.AMP, amp)
    external.set(M8ExternalParam.LIMIT, limit)
    external.set(M8ExternalParam.PAN, pan)
    external.set(M8ExternalParam.DRY, dry)
    external.set(M8ExternalParam.CHORUS_SEND, chorus)
    external.set(M8ExternalParam.DELAY_SEND, delay)
    external.set(M8ExternalParam.REVERB_SEND, reverb)

    return external


def print_external_parameters(external):
    """Print all External instrument parameters for verification."""
    print("\n" + "=" * 60)
    print("EXTERNAL INSTRUMENT PARAMETERS")
    print("=" * 60)
    print(f"Name: {external.name}")
    print()

    # MIDI params
    print("--- MIDI Parameters (displayed as decimal on device) ---")
    input_val = external.get(M8ExternalParam.INPUT)
    port_val = external.get(M8ExternalParam.PORT)
    print(f"  INPUT:       {input_val:3d} ({M8ExternalInput(input_val).name})")
    print(f"  PORT:        {port_val:3d} ({M8ExternalPort(port_val).name})")
    print(f"  CHANNEL:     {external.get(M8ExternalParam.CHANNEL):3d}")
    print(f"  BANK:        {external.get(M8ExternalParam.BANK):3d}")
    print(f"  PROGRAM:     {external.get(M8ExternalParam.PROGRAM):3d}")
    print()

    # CC params
    print("--- CC Parameters (CC number : CC value) ---")
    print(f"  CCA:         {external.get(M8ExternalParam.CCA_NUM):03d} : {external.get(M8ExternalParam.CCA_VAL):3d} (0x{external.get(M8ExternalParam.CCA_VAL):02X})")
    print(f"  CCB:         {external.get(M8ExternalParam.CCB_NUM):03d} : {external.get(M8ExternalParam.CCB_VAL):3d} (0x{external.get(M8ExternalParam.CCB_VAL):02X})")
    print(f"  CCC:         {external.get(M8ExternalParam.CCC_NUM):03d} : {external.get(M8ExternalParam.CCC_VAL):3d} (0x{external.get(M8ExternalParam.CCC_VAL):02X})")
    print(f"  CCD:         {external.get(M8ExternalParam.CCD_NUM):03d} : {external.get(M8ExternalParam.CCD_VAL):3d} (0x{external.get(M8ExternalParam.CCD_VAL):02X})")
    print()

    # Filter params
    print("--- Filter Parameters ---")
    filter_type = external.get(M8ExternalParam.FILTER_TYPE)
    print(f"  FILTER_TYPE: {filter_type:3d} (0x{filter_type:02X}) ({M8FilterType(filter_type).name})")
    print(f"  CUTOFF:      {external.get(M8ExternalParam.CUTOFF):3d} (0x{external.get(M8ExternalParam.CUTOFF):02X})")
    print(f"  RESONANCE:   {external.get(M8ExternalParam.RESONANCE):3d} (0x{external.get(M8ExternalParam.RESONANCE):02X})")
    print()

    # Mixer params
    print("--- Mixer Parameters ---")
    limit_val = external.get(M8ExternalParam.LIMIT)
    print(f"  AMP:         {external.get(M8ExternalParam.AMP):3d} (0x{external.get(M8ExternalParam.AMP):02X})")
    print(f"  LIMIT:       {limit_val:3d} (0x{limit_val:02X}) ({M8LimiterType(limit_val).name})")
    print(f"  PAN:         {external.get(M8ExternalParam.PAN):3d} (0x{external.get(M8ExternalParam.PAN):02X})")
    print(f"  DRY:         {external.get(M8ExternalParam.DRY):3d} (0x{external.get(M8ExternalParam.DRY):02X})")
    print(f"  CHORUS_SEND: {external.get(M8ExternalParam.CHORUS_SEND):3d} (0x{external.get(M8ExternalParam.CHORUS_SEND):02X})")
    print(f"  DELAY_SEND:  {external.get(M8ExternalParam.DELAY_SEND):3d} (0x{external.get(M8ExternalParam.DELAY_SEND):02X})")
    print(f"  REVERB_SEND: {external.get(M8ExternalParam.REVERB_SEND):3d} (0x{external.get(M8ExternalParam.REVERB_SEND):02X})")
    print("=" * 60)


def create_external_test_project():
    """Create the External test M8 project."""
    print(f"Creating External test demo: {PROJECT_NAME}")
    print(f"BPM: {BPM}, Seed: {SEED}")

    # Initialize RNG with seed for reproducible results
    rng = random.Random(SEED)

    # Initialize project
    project = M8Project.initialise()
    project.metadata.name = PROJECT_NAME
    project.metadata.tempo = BPM
    project.metadata.directory = "/Songs/pym8-demos/external-test/"

    # Create External instrument with randomized parameters
    external = create_test_external_instrument(rng)
    project.instruments[0] = external

    # Print all parameters for verification
    print_external_parameters(external)

    # Create phrase with C-4 note on step 0
    phrase = M8Phrase()
    phrase[0] = M8PhraseStep(
        note=M8Note.C_4,
        velocity=0x7F,
        instrument=0x00
    )
    project.phrases[0] = phrase
    print(f"\nPhrase 0x00: C-4 note on step 0, instrument 0x00")

    # Create chain referencing phrase 0
    chain = M8Chain()
    chain[0] = M8ChainStep(phrase=0x00, transpose=0x00)
    project.chains[0] = chain
    print(f"Chain 0x00: references phrase 0x00")

    # Add chain to song at row 0, track 0
    project.song[0][0] = 0x00
    print(f"Song: chain 0x00 at row 0, track 0")

    return project


def save_project(project: M8Project):
    """Save the M8 project."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    output_path = OUTPUT_DIR / f"{PROJECT_NAME}.m8s"
    print(f"\nSaving project to {output_path}...")
    project.write_to_file(str(output_path))

    print(f"\nDemo complete!")
    print(f"  Project: {output_path}")
    print(f"\nLoad this file on your M8 and verify each parameter matches the values above.")


def main():
    """Main entry point."""
    project = create_external_test_project()
    save_project(project)


if __name__ == '__main__':
    main()
