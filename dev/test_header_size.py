#!/usr/bin/env python3
"""
Test M8i Header Size: 12 vs 14 bytes

This script tests whether the M8i header is 12 or 14 bytes by checking where
the modulators actually are and whether they match the expected values.
"""

import sys
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

m8i_path = Path("tmp/dw01-synthdrums/m8i/KICK_MORPH.m8i")

with open(m8i_path, 'rb') as f:
    data = f.read()

print("=" * 70)
print("M8i HEADER SIZE TEST")
print("=" * 70)
print()

# Expected modulator 0 values (from YAML)
expected_mod0 = {
    'type': 0x00,        # AHD_ENVELOPE
    'destination': 0x01, # VOLUME
    'amount': 0xFF,      # 255
    'attack': 0x00,      # 0
    'hold': 0x00,        # 0
    'decay': 0x60,       # 96
}

print("Expected Modulator 0 (from YAML):")
print(f"  Type: {expected_mod0['type']} (AHD_ENVELOPE)")
print(f"  Destination: {expected_mod0['destination']} (VOLUME)")
print(f"  Amount: {expected_mod0['amount']}")
print(f"  Attack: {expected_mod0['attack']}")
print(f"  Hold: {expected_mod0['hold']}")
print(f"  Decay: {expected_mod0['decay']}")
print()

# Test hypothesis 1: Header = 14 bytes, modulators at instrument offset 61
print("=" * 70)
print("HYPOTHESIS 1: Header = 14 bytes")
print("=" * 70)
header_size = 14
mod_offset_in_instrument = 61
file_offset = header_size + mod_offset_in_instrument
print(f"  Header size: {header_size} bytes")
print(f"  Instrument starts at file offset: {header_size}")
print(f"  Modulators at instrument offset: {mod_offset_in_instrument}")
print(f"  Modulators at file offset: {file_offset}")
print()

# Read M8i format: dest, amt, atk, hold, dec, ???
mod0_bytes_h1 = data[file_offset:file_offset+6]
print(f"  Raw bytes: {' '.join(f'{b:02X}' for b in mod0_bytes_h1)}")
print(f"  Parsed:")
print(f"    Destination: 0x{mod0_bytes_h1[0]:02X} ({mod0_bytes_h1[0]})")
print(f"    Amount: 0x{mod0_bytes_h1[1]:02X} ({mod0_bytes_h1[1]})")
print(f"    Attack: 0x{mod0_bytes_h1[2]:02X} ({mod0_bytes_h1[2]})")
print(f"    Hold: 0x{mod0_bytes_h1[3]:02X} ({mod0_bytes_h1[3]})")
print(f"    Decay: 0x{mod0_bytes_h1[4]:02X} ({mod0_bytes_h1[4]})")

# Check if it matches
matches_h1 = (
    mod0_bytes_h1[0] == expected_mod0['destination'] and
    mod0_bytes_h1[1] == expected_mod0['amount'] and
    mod0_bytes_h1[2] == expected_mod0['attack'] and
    mod0_bytes_h1[3] == expected_mod0['hold'] and
    mod0_bytes_h1[4] == expected_mod0['decay']
)
print(f"  MATCH: {matches_h1}")
print()

# Test hypothesis 2: Header = 12 bytes, modulators at instrument offset 63
print("=" * 70)
print("HYPOTHESIS 2: Header = 12 bytes")
print("=" * 70)
header_size = 12
mod_offset_in_instrument = 63
file_offset = header_size + mod_offset_in_instrument
print(f"  Header size: {header_size} bytes")
print(f"  Instrument starts at file offset: {header_size}")
print(f"  Modulators at instrument offset: {mod_offset_in_instrument}")
print(f"  Modulators at file offset: {file_offset}")
print()

# Read M8i format: dest, amt, atk, hold, dec, ???
mod0_bytes_h2 = data[file_offset:file_offset+6]
print(f"  Raw bytes: {' '.join(f'{b:02X}' for b in mod0_bytes_h2)}")
print(f"  Parsed:")
print(f"    Destination: 0x{mod0_bytes_h2[0]:02X} ({mod0_bytes_h2[0]})")
print(f"    Amount: 0x{mod0_bytes_h2[1]:02X} ({mod0_bytes_h2[1]})")
print(f"    Attack: 0x{mod0_bytes_h2[2]:02X} ({mod0_bytes_h2[2]})")
print(f"    Hold: 0x{mod0_bytes_h2[3]:02X} ({mod0_bytes_h2[3]})")
print(f"    Decay: 0x{mod0_bytes_h2[4]:02X} ({mod0_bytes_h2[4]})")

# Check if it matches
matches_h2 = (
    mod0_bytes_h2[0] == expected_mod0['destination'] and
    mod0_bytes_h2[1] == expected_mod0['amount'] and
    mod0_bytes_h2[2] == expected_mod0['attack'] and
    mod0_bytes_h2[3] == expected_mod0['hold'] and
    mod0_bytes_h2[4] == expected_mod0['decay']
)
print(f"  MATCH: {matches_h2}")
print()

# Conclusion
print("=" * 70)
print("CONCLUSION")
print("=" * 70)
if matches_h1 and not matches_h2:
    print("✓ Header is 14 bytes, FM synth modulators at instrument offset 61")
elif matches_h2 and not matches_h1:
    print("✓ Header is 12 bytes, FM synth modulators at instrument offset 63")
elif matches_h1 and matches_h2:
    print("✓ Both match! (file offset 75 in both cases)")
    print("  We should use header=12, offset=63 for consistency with M8s format")
else:
    print("✗ Neither matches! Something is wrong.")
print()

# Show what bytes 12-13 contain
print("What are bytes 12-13?")
print(f"  Byte 12: 0x{data[12]:02X} ({data[12]:3d})")
print(f"  Byte 13: 0x{data[13]:02X} ({data[13]:3d})")
print()
if data[12] == 0x00:
    print("  Byte 12 is 0x00 (expected 4th version byte)")
if data[13] == data[14]:
    print(f"  Byte 13 (0x{data[13]:02X}) == Byte 14 (0x{data[14]:02X}) = instrument type!")
    print(f"  This suggests byte 13 might be part of instrument, not header")
