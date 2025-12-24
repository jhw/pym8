#!/usr/bin/env python
"""Reverse engineer wavsynth parameter offsets from test file."""

from m8.api.project import M8Project

# Known values from user
KNOWN_VALUES = {
    'SHAPE': 0x09,
    'SIZE': 0x0A,
    'MULT': 0x0B,
    'WARP': 0x0C,
    'SCAN': 0x0D,
    'FILTER': 0x0A,
    'CUTOFF': 0x0E,
    'RESONANCE': 0x0F,
    'AMP': 0x10,
    'LIM': 0x07,
    'PAN': 0x11,
    'DRY': 0x12,
    'MFX': 0x13,
    'DEL': 0x14,
    'REV': 0x15,
}

MODULATOR_DESTINATIONS = {
    0: 0x01,  # VOLUME
    1: 0x04,  # MULT
    2: 0x02,  # PITCH
    3: 0x05,  # WARP
}

print("=" * 70)
print("REVERSE ENGINEERING WAVSYNTH PARAMETER OFFSETS")
print("=" * 70)
print()

# Load the test file
project = M8Project.read_from_file('tmp/plasticant.m8s')
inst = project.instruments[0]

print("Instrument 0 type:", hex(inst._data[0]))
print("Instrument 0 name:", inst.name)
print()

# Print first 100 bytes to see the structure
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
print("MODULATOR DESTINATIONS:")
print("=" * 70)

for mod_idx in range(4):
    offset = 63 + (mod_idx * 23)
    if offset < len(inst._data):
        type_dest = inst._data[offset]
        mod_type = (type_dest >> 4) & 0x0F
        dest = type_dest & 0x0F

        expected_dest = MODULATOR_DESTINATIONS[mod_idx]
        match_str = "✓" if dest == expected_dest else f"✗ (expected {expected_dest:02X})"

        print(f"Mod {mod_idx}: type={mod_type:02X}, dest={dest:02X} {match_str}")

print()
