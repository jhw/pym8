#!/usr/bin/env python
"""Verify modulator destinations are read correctly."""

from m8.api.project import M8Project

project = M8Project.read_from_file('tmp/plasticant.m8s')
inst = project.instruments[0]

print("=" * 70)
print("MODULATOR VERIFICATION")
print("=" * 70)
print()

for mod_idx in range(4):
    offset = 63 + (mod_idx * 23)

    # Read directly from instrument _data
    raw_byte = inst._data[offset]
    raw_type = (raw_byte >> 4) & 0x0F
    raw_dest = raw_byte & 0x0F

    # Read via modulator object
    mod = inst.modulators[mod_idx]
    prop_type = mod.mod_type
    prop_dest = mod.destination

    # Read from modulator's own _data
    mod_byte = mod._data[0]
    mod_type = (mod_byte >> 4) & 0x0F
    mod_dest = mod_byte & 0x0F

    print(f"Modulator {mod_idx}:")
    print(f"  From inst._data[{offset}]:         0x{raw_byte:02X} -> type={raw_type:X}, dest={raw_dest:X}")
    print(f"  From mod._data[0]:                0x{mod_byte:02X} -> type={mod_type:X}, dest={mod_dest:X}")
    print(f"  Via properties:                   type={prop_type:X}, dest={prop_dest:X}")
    print()

expected = [0x01, 0x04, 0x02, 0x05]
print("Expected destinations: 0x01, 0x04, 0x02, 0x05")
print("Actual destinations:  ", end="")
for i in range(4):
    print(f" 0x{inst.modulators[i].destination:02X}", end="")
print()
print()

all_correct = all(inst.modulators[i].destination == expected[i] for i in range(4))
print("✓ All modulators correct!" if all_correct else "✗ Modulators incorrect")
