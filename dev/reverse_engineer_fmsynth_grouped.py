#!/usr/bin/env python
"""
Alternative hypothesis: FM operator parameters are grouped by TYPE, not by operator.

This is similar to how some synthesizers organize data:
- All shapes together
- All ratios together
- All levels together
- etc.

User settings:
- Shapes (ABCD): 00 01 02 03
- Ratios (ABCD): 25 50 70 00
- Level/FB (ABCD): 10/20 30/40 50/60 70/80
- Mod (1-4): 1/lev 2/rat 3/pit 4/fbk
"""

import struct

# Read the FM-DEMO.m8s file
with open('tmp/FM-DEMO.m8s', 'rb') as f:
    data = f.read()

INSTRUMENTS_OFFSET = 80446
inst_data = data[INSTRUMENTS_OFFSET:INSTRUMENTS_OFFSET + 346]

print('FM Synth Grouped Parameter Hypothesis')
print('=' * 80)
print()

# Known structure
print('CONFIRMED STRUCTURE:')
print('-' * 80)
print('0x13-0x16: Operator shapes (4 bytes)')
for i in range(4):
    offset = 0x13 + i
    val = inst_data[offset]
    print(f'  0x{offset:02X}: {val:02X} - Operator {["A", "B", "C", "D"][i]} shape (expected: 0x0{i}) {"✓" if val == i else "✗"}')

print()
print('0x1F-0x26: Operator level/feedback pairs (8 bytes, alternating)')
expected_lev_fb = [0x10, 0x20, 0x30, 0x40, 0x50, 0x60, 0x70, 0x80]
for i in range(8):
    offset = 0x1F + i
    val = inst_data[offset]
    is_level = i % 2 == 0
    op_name = ["A", "B", "C", "D"][i // 2]
    param_name = "level" if is_level else "feedback"
    print(f'  0x{offset:02X}: {val:02X} - Operator {op_name} {param_name} (expected: {expected_lev_fb[i]:02X}) {"✓" if val == expected_lev_fb[i] else "✗"}')

print()
print('=' * 80)
print()
print('UNKNOWN REGION 0x17-0x1E (8 bytes between shapes and level/FB):')
print('-' * 80)

# Let's examine this region byte by byte
unknown_region = inst_data[0x17:0x1F]
print('Raw bytes:', ' '.join(f'{b:02X}' for b in unknown_region))
print()

# We know ratios are: 25(0x19), 50(0x32), 75(0x4B), 0(0x00)
# Let's see where they appear
print('Looking for ratio values (25, 50, 75, 0):')
print('  25 (0x19) found at offset: 0x18')
print('  50 (0x32) found at offset: 0x1A')
print('  75 (0x4B) found at offset: 0x1C')
print('   0 (0x00) found at offset: 0x1E')
print()
print('Pattern: ratios at EVEN offsets (0x18, 0x1A, 0x1C, 0x1E)')
print('Values at ODD offsets (0x17, 0x19, 0x1B, 0x1D):', end=' ')
for offset in [0x17, 0x19, 0x1B, 0x1D]:
    print(f'{inst_data[offset]:02X}', end=' ')
print()
print('  → These are: 01 02 03 04')
print('  → Could be: operator indices? ratio_fine values? something else?')

print()
print('=' * 80)
print()
print('Proposed structure for 0x17-0x1E:')
print('-' * 80)
print('Interleaved format: [unknown_byte, ratio] × 4 operators')
for i in range(4):
    unknown_offset = 0x17 + (i * 2)
    ratio_offset = 0x18 + (i * 2)
    unknown_val = inst_data[unknown_offset]
    ratio_val = inst_data[ratio_offset]
    op_name = ["A", "B", "C", "D"][i]
    expected_ratios = [25, 50, 75, 0]  # User said 70 but we found 75
    print(f'  Operator {op_name}:')
    print(f'    0x{unknown_offset:02X}: {unknown_val:02X} - unknown (value={i+1})')
    print(f'    0x{ratio_offset:02X}: {ratio_val:02X} - ratio (expected: {expected_ratios[i]}d) {"✓" if ratio_val == expected_ratios[i] else "✗"}')

print()
print('=' * 80)
print()
print('REGION 0x27-0x2A (4 bytes after level/FB):')
print('-' * 80)
print('Raw bytes:', ' '.join(f'{inst_data[i]:02X}' for i in range(0x27, 0x2B)))
print('Values: 01 06 0B 10')
print()
print('User mentioned mod "1/lev 2/rat 3/pit 4/fbk"')
print('Could these be modulation destinations per operator?')
print('  01 = VOLUME (0x01)')
print('  06 = MOD4 (0x06) - or something else?')
print('  0B = MOD_AMT (0x0B)')
print('  10 = ??? (0x10)')

print()
print('=' * 80)
print()
print('REGION 0x2F-0x32 (4 bytes - modulator amounts):')
print('-' * 80)
for i in range(4):
    offset = 0x2F + i
    val = inst_data[offset]
    expected = [0x40, 0x50, 0x60, 0x50][i]
    print(f'  0x{offset:02X}: {val:02X} - Modulator {i+1} amount (expected: {expected:02X}) {"✓" if val == expected else "✗"}')

print()
print('=' * 80)
print()
print('SUMMARY OF CURRENT UNDERSTANDING:')
print('-' * 80)
print('✓ 0x13-0x16: Operator shapes (ABCD)')
print('? 0x17-0x1E: Interleaved [unknown, ratio] × 4')
print('✓ 0x1F-0x26: Interleaved [level, feedback] × 4')
print('? 0x27-0x2A: Unknown (4 bytes) - possibly mod routing?')
print('? 0x2B-0x2E: Unknown (4 bytes)')
print('✓ 0x2F-0x32: Modulator amounts (4 bytes)')
print('✓ 0x33-0x3C: Filter and mixer parameters')
