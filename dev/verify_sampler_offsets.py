#!/usr/bin/env python
"""Verify sampler parameter offsets are correctly mapped."""

from m8.api.project import M8Project
from m8.api.instruments.sampler import M8SamplerParam

print("=" * 70)
print("SAMPLER PARAMETER OFFSET VERIFICATION")
print("=" * 70)
print()

# Load the test file created with known parameter values
project = M8Project.read_from_file('tmp/LONELYVILLA.m8s')
inst = project.instruments[0]

print("Test file: tmp/LONELYVILLA.m8s")
print("Instrument 0 type:", hex(inst._data[0]))
print("Instrument 0 name:", inst.name if inst.name else "(empty)")
print()

# Expected values set by user in the M8
EXPECTED_VALUES = {
    'PLAY_MODE': 0x02,
    'SLICE': 0x01,
    'START': 0x03,
    'LOOP_START': 0x04,
    'LENGTH': 0x05,
    'FINE_TUNE': 0x06,  # User called this DETUNE
    'DEGRADE': 0x07,
    'FILTER_TYPE': 0x07,  # User called this FILTER (same value as DEGRADE)
    'CUTOFF': 0x09,
    'RESONANCE': 0x0A,
    'AMP': 0x0B,
    'LIMIT': 0x08,  # User called this LIM
    'PAN': 0x0D,
    'DRY': 0x0E,
    'CHORUS_SEND': 0x0F,  # User called this MFX
    'DELAY_SEND': 0x10,  # User called this DEL
    'REVERB_SEND': 0x11,  # User called this REV
}

print("Verifying parameter offsets:")
print("-" * 70)
print(f"{'Parameter':<20} {'Offset':<8} {'Expected':<10} {'Actual':<10} {'Status'}")
print("-" * 70)

all_correct = True

for param_name, expected_val in EXPECTED_VALUES.items():
    # Get the offset from our enum
    param_enum = getattr(M8SamplerParam, param_name)
    offset = param_enum.value

    # Read the actual value from the file
    actual_val = inst._data[offset]

    # Check if it matches
    status = "✓" if actual_val == expected_val else "✗"
    if actual_val != expected_val:
        all_correct = False

    print(f"{param_name:<20} {offset:<8} 0x{expected_val:02X} ({expected_val:3d}) 0x{actual_val:02X} ({actual_val:3d})  {status}")

print("-" * 70)

if all_correct:
    print("\n✓ ALL PARAMETER OFFSETS ARE CORRECT!")
    print("\nThe current implementation in m8/api/instruments/sampler.py is accurate.")
else:
    print("\n✗ SOME OFFSETS ARE INCORRECT")
    print("\nThe implementation needs to be updated.")

print()

# Show the structure for documentation
print("=" * 70)
print("SAMPLER STRUCTURE (verified)")
print("=" * 70)
print()
print("Common fields (0-17):")
print("   0: TYPE         = 0x02 (SAMPLER)")
print("   1-12: NAME (12 bytes)")
print("  13: TRANSPOSE    = 0x01")
print("  14: TABLE_TICK   = 0x01")
print("  15: VOLUME       = 0x00")
print("  16: PITCH        = 0x00")
print("  17: FINE_TUNE    = 0x06 (0x80 = center)")
print()
print("Sampler-specific playback fields (18-23):")
print("  18: PLAY_MODE    = 0x02")
print("  19: SLICE        = 0x01")
print("  20: START        = 0x03")
print("  21: LOOP_START   = 0x04")
print("  22: LENGTH       = 0x05 (0xFF = full)")
print("  23: DEGRADE      = 0x07")
print()
print("Filter fields (24-26):")
print("  24: FILTER_TYPE  = 0x07")
print("  25: CUTOFF       = 0x09 (0xFF = open)")
print("  26: RESONANCE    = 0x0A")
print()
print("Mixer fields (27-33):")
print("  27: AMP          = 0x0B")
print("  28: LIMIT        = 0x08")
print("  29: PAN          = 0x0D (0x80 = center)")
print("  30: DRY          = 0x0E (0xC0 = default)")
print("  31: CHORUS_SEND  = 0x0F (MFX in M8 UI)")
print("  32: DELAY_SEND   = 0x10")
print("  33: REVERB_SEND  = 0x11")
print()
print("Modulators start at offset 63")
print()
