#!/usr/bin/env python
"""
Reverse engineer FM Synth parameters from tmp/FM-DEMO.m8s

User settings:
- Algo: 0x0B (A+B+C+D)
- Operator types (ABCD): 00 01 02 03 (sine/half sine/third sine/quarter sine)
- Ratio (ABCD): 25 50 70 00 (decimal values)
- Lev/FB (ABCD): 10/20 30/40 50/60 70/80 (hex values)
- Mod (1-4): 1/lev 2/rat 3/pit 4/fbk
- Mod values (1-4): 40 50 60 50
- Filter: 07
- Cutoff: B0
- Resonance: C0
- Amp: 10
- Limiter: 04
- Pan: 80
- Dry: C0
- Chorus: 90
- Delay: 40
- Reverb: B0
"""

import struct

# Read the FM-DEMO.m8s file
with open('tmp/FM-DEMO.m8s', 'rb') as f:
    data = f.read()

# Instruments start at offset 80446
INSTRUMENTS_OFFSET = 80446
INSTRUMENT_SIZE = 346

# Read instrument 0
inst_offset = INSTRUMENTS_OFFSET
inst_data = data[inst_offset:inst_offset + INSTRUMENT_SIZE]

print('FM Synth Parameter Reverse Engineering')
print('=' * 70)
print()

# Known values to search for
known_values = {
    'algo': 0x0B,
    'ratios': [0x19, 0x32, 0x46, 0x00],  # 25, 50, 70, 0 decimal
    'ratios_alt': [0x19, 0x32, 0x4B, 0x00],  # 25, 50, 75, 0 (if user meant 75)
    'lev_fb': [0x10, 0x20, 0x30, 0x40, 0x50, 0x60, 0x70, 0x80],
    'filter': 0x07,
    'cutoff': 0xB0,
    'resonance': 0xC0,
    'amp': 0x10,
    'limiter': 0x04,
    'pan': 0x80,
    'dry': 0xC0,
    'chorus': 0x90,
    'delay': 0x40,
    'reverb': 0xB0,
}

print('Searching for known values:')
print()

# Search for algo
for i, byte in enumerate(inst_data):
    if byte == known_values['algo']:
        print(f'Algo 0x0B found at offset: {i} (0x{i:02X})')

# Search for lev/FB sequence
lev_fb_bytes = bytes(known_values['lev_fb'])
for i in range(len(inst_data) - len(lev_fb_bytes)):
    if inst_data[i:i+len(lev_fb_bytes)] == lev_fb_bytes:
        print(f'Lev/FB sequence found at offset: {i} (0x{i:02X}) to {i+7} (0x{i+7:02X})')

# Search for filter params
for i, byte in enumerate(inst_data):
    if byte == known_values['filter']:
        print(f'Filter 0x07 found at offset: {i} (0x{i:02X})')
    if byte == known_values['cutoff']:
        print(f'Cutoff 0xB0 found at offset: {i} (0x{i:02X})')
    if byte == known_values['resonance']:
        print(f'Resonance 0xC0 found at offset: {i} (0x{i:02X})')

# Search for mixer params
for i, byte in enumerate(inst_data):
    if byte == known_values['amp']:
        print(f'Amp 0x10 found at offset: {i} (0x{i:02X})')
    if byte == known_values['limiter']:
        print(f'Limiter 0x04 found at offset: {i} (0x{i:02X})')
    if byte == known_values['pan']:
        print(f'Pan 0x80 found at offset: {i} (0x{i:02X})')
    if byte == known_values['dry']:
        print(f'Dry 0xC0 found at offset: {i} (0x{i:02X})')
    if byte == known_values['chorus']:
        print(f'Chorus 0x90 found at offset: {i} (0x{i:02X})')
    if byte == known_values['delay']:
        print(f'Delay 0x40 found at offset: {i} (0x{i:02X})')
    if byte == known_values['reverb']:
        print(f'Reverb 0xB0 found at offset: {i} (0x{i:02X})')

print()
print('=' * 70)
print()
print('Full instrument data (first 80 bytes):')
print()
for i in range(0, min(80, len(inst_data)), 16):
    hex_str = ' '.join(f'{b:02X}' for b in inst_data[i:i+16])
    ascii_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in inst_data[i:i+16])
    annotations = []

    # Add annotations for known offsets
    if i == 0:
        annotations.append('TYPE, NAME')
    elif i == 16:
        annotations.append('TRANSPOSE, TABLE_TICK, VOL, PITCH, FINE_TUNE, ALGO, ...')
    elif i == 32:
        annotations.append('LEV/FB, MODS, ...')
    elif i == 48:
        annotations.append('MOD VALUES, FILTER, CUTOFF, RES, ...')
    elif i == 64:
        annotations.append('AMP, LIMIT, PAN, DRY, SENDS, ...')

    annotation = f'  # {", ".join(annotations)}' if annotations else ''
    print(f'{i:03d} (0x{i:02X}): {hex_str:<48} {ascii_str}{annotation}')

print()
print('Detailed parameter map:')
print()
print(f'Offset 0x00: {inst_data[0]:02X} = Type (0x04 = FMSYNTH)')
print(f'Offset 0x01-0x0C: Name (12 bytes)')
print(f'Offset 0x0D: {inst_data[0x0D]:02X} = Transpose')
print(f'Offset 0x0E: {inst_data[0x0E]:02X} = Table Tick')
print(f'Offset 0x0F: {inst_data[0x0F]:02X} = Volume')
print(f'Offset 0x10: {inst_data[0x10]:02X} = Pitch')
print(f'Offset 0x11: {inst_data[0x11]:02X} = Fine Tune')
print(f'Offset 0x12: {inst_data[0x12]:02X} = Algo')
print()
print('Operator structure (need to determine):')
print(f'Offsets 0x13-0x2E (28 bytes) - 4 operators x 7 bytes each?')
for i in range(0x13, 0x2F):
    print(f'  0x{i:02X}: {inst_data[i]:02X}', end='')
    if (i - 0x13 + 1) % 8 == 0:
        print()
    else:
        print(', ', end='')
