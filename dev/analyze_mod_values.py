#!/usr/bin/env python
"""Analyze mod_a and mod_b values from FM-DEMO.m8s"""

# Read the FM-DEMO.m8s file
with open('tmp/FM-DEMO.m8s', 'rb') as f:
    data = f.read()

INSTRUMENTS_OFFSET = 80446
inst_data = data[INSTRUMENTS_OFFSET:INSTRUMENTS_OFFSET + 346]

print("FM Synth Operator Modulation Analysis")
print("=" * 80)
print()

# mod_a values at 0x27-0x2A (4 bytes)
print("mod_a values (0x27-0x2A):")
mod_a_values = []
for i in range(4):
    offset = 0x27 + i
    val = inst_data[offset]
    mod_a_values.append(val)
    op_name = ["A", "B", "C", "D"][i]
    print(f"  Operator {op_name}: {val:02X} ({val:3d})")

print()

# mod_b values at 0x2B-0x2E (4 bytes)
print("mod_b values (0x2B-0x2E):")
mod_b_values = []
for i in range(4):
    offset = 0x2B + i
    val = inst_data[offset]
    mod_b_values.append(val)
    op_name = ["A", "B", "C", "D"][i]
    print(f"  Operator {op_name}: {val:02X} ({val:3d})")

print()
print("=" * 80)
print()

# Analyze pattern
print("Pattern analysis:")
print(f"  mod_a values: {' '.join(f'{v:02X}' for v in mod_a_values)} = {mod_a_values}")
print(f"  mod_b values: {' '.join(f'{v:02X}' for v in mod_b_values)} = {mod_b_values}")
print()

# Check spacing
if all(mod_a_values[i] > 0 for i in range(4)):
    diffs = [mod_a_values[i+1] - mod_a_values[i] for i in range(3)]
    print(f"  mod_a differences: {diffs}")
    if all(d == diffs[0] for d in diffs):
        print(f"  → Evenly spaced by {diffs[0]}")
    print()

# User's description
print("User's settings:")
print("  User said: '1/lev 2/rat 3/pit 4/fbk'")
print("  User suggested values might be: '00 05 0A 0F' (0, 5, 10, 15)")
print()
print("  Actual mod_a values: 01 06 0B 10 (1, 6, 11, 16)")
print("  → Off by 1 from user's suggestion!")
print()

# Hypothesis
print("Hypothesis:")
print("  If user set '00 05 0A 0F' but got '01 06 0B 10', there's an off-by-one error.")
print("  OR the user interface shows 0-indexed values but file stores 1-indexed.")
print()

# Check against known enums
print("Checking against FM_FX_BASE_COMMANDS (from Rust code):")
FM_FX = ["VOL", "PIT", "FIN", "ALG", "FM1", "FM2", "FM3", "FM4",
         "FLT", "CUT", "RES", "AMP", "LIM", "PAN", "DRY"]
print("  Index mapping:")
for i, val in enumerate(mod_a_values):
    op_name = ["A", "B", "C", "D"][i]
    if val < len(FM_FX):
        print(f"    Operator {op_name} mod_a={val:2d} → FM_FX[{val}] = {FM_FX[val]}")
    else:
        print(f"    Operator {op_name} mod_a={val:2d} → OUT OF RANGE (max index={len(FM_FX)-1})")
print()

print("Checking against DESTINATIONS (from Rust code):")
DESTINATIONS = ["OFF", "VOLUME", "PITCH", "MOD1", "MOD2", "MOD3", "MOD4",
                "CUTOFF", "RES", "AMP", "PAN", "MOD_AMT", "MOD_RATE", "MOD_BOTH", "MOD_BINV"]
print("  Index mapping:")
for i, val in enumerate(mod_a_values):
    op_name = ["A", "B", "C", "D"][i]
    if val < len(DESTINATIONS):
        print(f"    Operator {op_name} mod_a={val:2d} → DESTINATIONS[{val}] = {DESTINATIONS[val]}")
    else:
        print(f"    Operator {op_name} mod_a={val:2d} → OUT OF RANGE (max index={len(DESTINATIONS)-1})")
print()

print("=" * 80)
print()
print("CONCLUSION:")
print("  The mod_a value 16 (0x10) is OUT OF RANGE for both arrays!")
print("  This suggests mod_a/mod_b use a DIFFERENT enum that we haven't found yet,")
print("  OR they represent something other than array indices (offsets, parameter IDs, etc.)")
