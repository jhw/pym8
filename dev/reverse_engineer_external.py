#!/usr/bin/env python
"""
Reverse engineer External instrument parameters from tmp/EXTERNAL.m8s

User settings (hex values):
- Input: 01
- Port: 02
- Channel: 03
- Bank: 04 (decimal 4, displayed as 004)
- Program: 05 (decimal 5, displayed as 005)
- CCA: CC number=01, value=06
- CCB: CC number=02, value=07
- CCC: CC number=03, value=08
- CCD: CC number=04, value=09
- Filter: 07
- Cutoff: 0A
- Resonance: 0B
- Amp: 0C
- Limit: 08
- Pan: 0D
- Dry: 0E
- Chorus/MFX: 0F
- Delay: 10
- Reverb: 11

Type ID should be 0x06 (External) based on m8-file-parser
"""

import struct

# Read the EXTERNAL.m8s file
with open('tmp/EXTERNAL.m8s', 'rb') as f:
    data = f.read()

# Instruments start at offset 80446
INSTRUMENTS_OFFSET = 80446
INSTRUMENT_SIZE = 215

# Read instrument 0
inst_offset = INSTRUMENTS_OFFSET
inst_data = data[inst_offset:inst_offset + INSTRUMENT_SIZE]

print('External Instrument Parameter Reverse Engineering')
print('=' * 70)
print()

# Known values to search for
known_values = {
    'type': 0x06,  # External instrument type
    'input': 0x01,
    'port': 0x02,
    'channel': 0x03,
    'bank': 0x04,
    'program': 0x05,
    'cca_num': 0x01,
    'cca_val': 0x06,
    'ccb_num': 0x02,
    'ccb_val': 0x07,
    'ccc_num': 0x03,
    'ccc_val': 0x08,
    'ccd_num': 0x04,
    'ccd_val': 0x09,
    'filter': 0x07,
    'cutoff': 0x0A,
    'resonance': 0x0B,
    'amp': 0x0C,
    'limit': 0x08,
    'pan': 0x0D,
    'dry': 0x0E,
    'chorus': 0x0F,
    'delay': 0x10,
    'reverb': 0x11,
}

print(f'Instrument type byte at offset 0: 0x{inst_data[0]:02X}')
print()

print('Searching for known values:')
print()

# Search for each value
for name, value in known_values.items():
    matches = []
    for i, byte in enumerate(inst_data):
        if byte == value:
            matches.append(i)
    if matches:
        print(f'{name} (0x{value:02X}): found at offsets {matches}')
    else:
        print(f'{name} (0x{value:02X}): NOT FOUND')

print()
print('=' * 70)
print()
print('Full instrument data (first 80 bytes):')
print()
for i in range(0, min(80, len(inst_data)), 16):
    hex_str = ' '.join(f'{b:02X}' for b in inst_data[i:i+16])
    ascii_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in inst_data[i:i+16])
    print(f'{i:03d} (0x{i:02X}): {hex_str:<48} {ascii_str}')

print()
print('Detailed byte analysis:')
print()
print(f'Offset 0x00: 0x{inst_data[0]:02X} = Type')
print(f'Offset 0x01-0x0C: Name (12 bytes): "{inst_data[1:13].decode("utf-8", errors="replace").rstrip(chr(0))}"')
print(f'Offset 0x0D: 0x{inst_data[0x0D]:02X} = Transpose')
print(f'Offset 0x0E: 0x{inst_data[0x0E]:02X} = Table Tick')
print()

# Based on m8-file-parser, after common params we have:
# input, port, channel, bank, program, then CC params
print('External-specific params (searching):')
for i in range(0x0F, min(0x30, len(inst_data))):
    print(f'  0x{i:02X}: 0x{inst_data[i]:02X} ({inst_data[i]:3d})')

print()
print('Looking for filter/mixer sequence:')
# The filter/mixer section should be: filter, cutoff, res, amp, limit, pan, dry, chorus, delay, reverb
# Expected values: 07 0A 0B 0C 08 0D 0E 0F 10 11
expected_sequence = bytes([0x07, 0x0A, 0x0B, 0x0C, 0x08, 0x0D, 0x0E, 0x0F, 0x10, 0x11])
for i in range(len(inst_data) - len(expected_sequence)):
    if inst_data[i:i+len(expected_sequence)] == expected_sequence:
        print(f'Filter/mixer sequence found at offset {i} (0x{i:02X})')

# Also look for partial matches
print()
print('Looking for filter value (0x07) followed by cutoff (0x0A):')
for i in range(len(inst_data) - 1):
    if inst_data[i] == 0x07 and inst_data[i+1] == 0x0A:
        print(f'  Found at offset {i} (0x{i:02X})')

print()
print('Looking for MIDI params sequence (input=01, port=02, channel=03):')
for i in range(len(inst_data) - 2):
    if inst_data[i] == 0x01 and inst_data[i+1] == 0x02 and inst_data[i+2] == 0x03:
        print(f'  Found at offset {i} (0x{i:02X})')

print()
print('Looking for CC number/value pairs:')
print('  CCA: num=01, val=06')
for i in range(len(inst_data) - 1):
    if inst_data[i] == 0x01 and inst_data[i+1] == 0x06:
        print(f'    Found 01 06 at offset {i} (0x{i:02X})')

print('  CCB: num=02, val=07')
for i in range(len(inst_data) - 1):
    if inst_data[i] == 0x02 and inst_data[i+1] == 0x07:
        print(f'    Found 02 07 at offset {i} (0x{i:02X})')

print('  CCC: num=03, val=08')
for i in range(len(inst_data) - 1):
    if inst_data[i] == 0x03 and inst_data[i+1] == 0x08:
        print(f'    Found 03 08 at offset {i} (0x{i:02X})')

print('  CCD: num=04, val=09')
for i in range(len(inst_data) - 1):
    if inst_data[i] == 0x04 and inst_data[i+1] == 0x09:
        print(f'    Found 04 09 at offset {i} (0x{i:02X})')
