#!/usr/bin/env python
"""Verify the demo file has correct parameter values at correct offsets."""

from m8.api.project import M8Project
from m8.api.instruments.wavsynth import M8WavsynthParam, M8WavShape

# Read the demo file
project = M8Project.read_from_file('tmp/demos/wavsynth_303/WAVSYNTH-303.m8s')
inst = project.instruments[0]

print("=" * 70)
print("DEMO FILE VERIFICATION")
print("=" * 70)
print()

# Expected values from demo
expected = {
    'CUTOFF': (24, 0x20),
    'RESONANCE': (25, 0xC0),
    'SHAPE': (18, M8WavShape.SAW),  # 0x04
    'SIZE': (19, 0x20),  # default
    'PAN': (28, 0x80),  # default
    'DRY': (29, 0xC0),  # default
}

all_correct = True

for name, (offset, expected_val) in expected.items():
    actual_val = inst._data[offset]
    match = "✓" if actual_val == expected_val else "✗"
    if actual_val != expected_val:
        all_correct = False
    print(f"{name:12s} offset {offset:2d}: expected 0x{expected_val:02X}, got 0x{actual_val:02X} {match}")

print()
print("Modulators:")
mod0_dest = inst.modulators[0].destination
mod1_dest = inst.modulators[1].destination
mod1_amount = inst.modulators[1].amount
mod1_decay = inst.modulators[1].get(4)

print(f"  Mod 0 dest: {mod0_dest} (expected 1 VOLUME) {'✓' if mod0_dest == 1 else '✗'}")
print(f"  Mod 1 dest: {mod1_dest} (expected 7 CUTOFF) {'✓' if mod1_dest == 7 else '✗'}")
print(f"  Mod 1 amount: {mod1_amount} (expected 127) {'✓' if mod1_amount == 127 else '✗'}")
print(f"  Mod 1 decay: {mod1_decay} (expected 64) {'✓' if mod1_decay == 64 else '✗'}")

if mod0_dest != 1 or mod1_dest != 7 or mod1_amount != 127 or mod1_decay != 64:
    all_correct = False

print()
if all_correct:
    print("✓ All parameters correct!")
else:
    print("✗ Some parameters incorrect!")
