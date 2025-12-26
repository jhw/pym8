#!/usr/bin/env python
"""
Detailed reverse engineering of FM Synth operator structure.

User settings:
- Operator shapes (ABCD): 00 01 02 03
- Operator ratios (ABCD): 25 50 70 00 (decimal)
- Operator level/FB (ABCD): 10/20 30/40 50/60 70/80 (hex pairs)
- Mod values (1-4): 1/lev 2/rat 3/pit 4/fbk
  - These might be mod_a and mod_b per operator?
  - Or modulation routing?

From Rust m8-file-parser Operator struct:
- shape: FMWave (1 byte enum)
- ratio: u8
- ratio_fine: u8
- level: u8
- feedback: u8
- retrigger: u8
- mod_a: u8
- mod_b: u8

Total: 8 bytes per operator × 4 operators = 32 bytes
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

print('FM Synth Detailed Operator Reverse Engineering')
print('=' * 80)
print()

# We know operators are somewhere after ALGO (0x12)
# Let's look at the region from 0x13 to 0x40
print('Instrument data from offset 0x13 to 0x40 (operator region):')
print()

for i in range(0x13, 0x40):
    byte_val = inst_data[i]
    hex_str = f'{byte_val:02X}'
    dec_str = f'{byte_val:3d}'

    # Add annotations for known values
    annotations = []

    # Operator shapes
    if i == 0x13:
        annotations.append('OP_A_SHAPE=0x00 (SIN)')
    elif i == 0x14:
        annotations.append('OP_B_SHAPE=0x01 (SW2)')
    elif i == 0x15:
        annotations.append('OP_C_SHAPE=0x02 (SW3)')
    elif i == 0x16:
        annotations.append('OP_D_SHAPE=0x03 (SW4)')

    # Check for ratio values (25, 50, 70/75, 0)
    if byte_val == 0x19:  # 25 decimal
        annotations.append('VALUE=25 (ratio A?)')
    elif byte_val == 0x32:  # 50 decimal
        annotations.append('VALUE=50 (ratio B?)')
    elif byte_val == 0x46:  # 70 decimal
        annotations.append('VALUE=70 (ratio C?)')
    elif byte_val == 0x4B:  # 75 decimal
        annotations.append('VALUE=75 (ratio C? user said 70)')

    # Level/FB values
    if i >= 0x1F and i <= 0x26:
        if (i - 0x1F) % 2 == 0:
            op_name = ['A', 'B', 'C', 'D'][(i - 0x1F) // 2]
            annotations.append(f'OP_{op_name}_LEVEL={hex_str}')
        else:
            op_name = ['A', 'B', 'C', 'D'][(i - 0x1F) // 2]
            annotations.append(f'OP_{op_name}_FEEDBACK={hex_str}')

    # Print the byte
    annotation_str = '  # ' + ', '.join(annotations) if annotations else ''
    print(f'  0x{i:02X}: {hex_str} ({dec_str}){annotation_str}')

print()
print('=' * 80)
print()
print('Analyzing potential operator structure:')
print()

# Hypothesis 1: Operators are 8 bytes each, starting at 0x13
print('Hypothesis 1: 4 operators × 8 bytes = 32 bytes (0x13-0x32)')
print()

for op_idx in range(4):
    start_offset = 0x13 + (op_idx * 8)
    end_offset = start_offset + 8
    op_bytes = inst_data[start_offset:end_offset]

    op_name = ['A', 'B', 'C', 'D'][op_idx]
    print(f'Operator {op_name} (0x{start_offset:02X}-0x{end_offset-1:02X}):')

    for j, byte in enumerate(op_bytes):
        field_offset = start_offset + j
        field_names = ['shape', 'ratio', 'ratio_fine', 'level', 'feedback', 'retrigger', 'mod_a', 'mod_b']
        field_name = field_names[j] if j < len(field_names) else 'unknown'
        print(f'  [{j}] 0x{field_offset:02X}: {byte:02X} ({byte:3d}) - {field_name}')
    print()

print('=' * 80)
print()
print('Checking hypothesis against known values:')
print()

# Check if hypothesis matches known values
for op_idx in range(4):
    start_offset = 0x13 + (op_idx * 8)
    op_bytes = inst_data[start_offset:start_offset + 8]
    op_name = ['A', 'B', 'C', 'D'][op_idx]

    shape = op_bytes[0]
    ratio = op_bytes[1]
    ratio_fine = op_bytes[2]
    level = op_bytes[3]
    feedback = op_bytes[4]
    retrigger = op_bytes[5]
    mod_a = op_bytes[6]
    mod_b = op_bytes[7]

    print(f'Operator {op_name}:')
    print(f'  shape={shape:02X} (expected: 0x0{op_idx}): {"✓" if shape == op_idx else "✗"}')

    # Check ratios
    expected_ratios = [25, 50, 70, 0]  # User said 70, but we found 75
    actual_ratios_hex = [0x19, 0x32, 0x4B, 0x00]  # What we found: 25, 50, 75, 0
    print(f'  ratio={ratio:02X} ({ratio}d) (expected: {expected_ratios[op_idx]}d / 0x{actual_ratios_hex[op_idx]:02X}): {"✓" if ratio == actual_ratios_hex[op_idx] else "✗"}')

    # Check level/feedback
    expected_levels = [0x10, 0x30, 0x50, 0x70]
    expected_feedbacks = [0x20, 0x40, 0x60, 0x80]
    print(f'  level={level:02X} (expected: {expected_levels[op_idx]:02X}): {"✓" if level == expected_levels[op_idx] else "✗"}')
    print(f'  feedback={feedback:02X} (expected: {expected_feedbacks[op_idx]:02X}): {"✓" if feedback == expected_feedbacks[op_idx] else "✗"}')

    print(f'  ratio_fine={ratio_fine:02X}')
    print(f'  retrigger={retrigger:02X}')
    print(f'  mod_a={mod_a:02X}')
    print(f'  mod_b={mod_b:02X}')
    print()

print('=' * 80)
print()
print('User mentioned mod values "1/lev 2/rat 3/pit 4/fbk":')
print('  This might mean:')
print('    Mod 1: destination=level')
print('    Mod 2: destination=ratio')
print('    Mod 3: destination=pitch')
print('    Mod 4: destination=feedback')
print()
print('  Or it could mean mod_a/mod_b routing for each operator?')
print()
print('Looking at bytes after operators (0x33 onwards):')
for i in range(0x33, 0x40):
    print(f'  0x{i:02X}: {inst_data[i]:02X}')
