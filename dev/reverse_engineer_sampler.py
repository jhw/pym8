#!/usr/bin/env python
"""Reverse engineer sampler parameter offsets from test file."""

from m8.api.project import M8Project

# Known values from user for LONELYVILLA.m8s
# User set these specific values to unique hex values for identification
KNOWN_VALUES = {
    'SLICE': 0x01,
    'PLAY': 0x02,
    'START': 0x03,
    'LOOP_START': 0x04,
    'LENGTH': 0x05,
    'DETUNE': 0x06,
    'DEGRADE': 0x07,
    'FILTER': 0x07,  # Note: same as DEGRADE
    'CUTOFF': 0x09,
    'RESONANCE': 0x0A,
    'AMP': 0x0B,
    'LIM': 0x08,
    'PAN': 0x0D,
    'DRY': 0x0E,
    'MFX': 0x0F,
    'DEL': 0x10,
    'REV': 0x11,
}

print("=" * 70)
print("REVERSE ENGINEERING SAMPLER PARAMETER OFFSETS")
print("=" * 70)
print()

# Load the test file
project = M8Project.read_from_file('tmp/LONELYVILLA.m8s')
inst = project.instruments[0]

print("Instrument 0 type:", hex(inst._data[0]))
print("Instrument 0 name:", inst.name)
print()

# Print first 50 bytes to see the structure
print("First 50 bytes of instrument 0:")
print("Offset | Hex  | Dec | Matches")
print("-------|------|-----|-------------------")

found_offsets = {}

for i in range(50):
    val = inst._data[i]
    matches = []

    for param_name, expected_val in KNOWN_VALUES.items():
        if val == expected_val:
            matches.append(param_name)
            if param_name not in found_offsets:
                found_offsets[param_name] = []
            found_offsets[param_name].append(i)

    match_str = ", ".join(matches) if matches else ""
    print(f"  {i:2d}   | 0x{val:02X} | {val:3d} | {match_str}")

print()
print("=" * 70)
print("FOUND PARAMETER OFFSETS:")
print("=" * 70)

# Resolve duplicates by context
for param_name in sorted(KNOWN_VALUES.keys()):
    if param_name in found_offsets:
        offsets = found_offsets[param_name]
        if len(offsets) == 1:
            print(f"{param_name:12s} = {offsets[0]:2d} (0x{inst._data[offsets[0]]:02X})")
        else:
            print(f"{param_name:12s} = {offsets} (multiple matches, need disambiguation)")
    else:
        print(f"{param_name:12s} = NOT FOUND")

print()
print("=" * 70)
print("CURRENT IMPLEMENTATION OFFSETS (from sampler.py):")
print("=" * 70)
print("""
    PLAY_MODE = 18    # Sample playback mode
    SLICE = 19        # Slice selection
    START = 20        # Sample start position
    LOOP_START = 21   # Loop start position
    LENGTH = 22       # Sample length (0xFF = full)
    DEGRADE = 23      # Bitcrusher amount
    FILTER_TYPE = 24  # Filter type selection
    CUTOFF = 25       # Filter cutoff frequency (0xFF = open)
    RESONANCE = 26    # Filter resonance
    AMP = 27          # Amplifier level
    LIMIT = 28        # Limiter amount
    PAN = 29          # Stereo pan (0x80 = center)
    DRY = 30          # Dry/wet mix level
    CHORUS_SEND = 31  # Send to chorus effect
    DELAY_SEND = 32   # Send to delay effect
    REVERB_SEND = 33  # Send to reverb effect
""")

print()
