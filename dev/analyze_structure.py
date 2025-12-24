#!/usr/bin/env python
"""Analyze the complete structure to determine field order."""

from m8.api.project import M8Project

project = M8Project.read_from_file('tmp/plasticant.m8s')
inst = project.instruments[0]

print("=" * 70)
print("WAVSYNTH STRUCTURE ANALYSIS")
print("=" * 70)
print()

print("Based on the test file, the correct offsets are:")
print()
print("Common fields (0-17):")
print("  0:  TYPE       = 0x00 (WAVSYNTH)")
print("  1-12: NAME (12 bytes)")
print("  13: TRANSPOSE  = 0x01")
print("  14: TABLE_TICK = 0x01")
print("  15: VOLUME     = 0x00")
print("  16: PITCH      = 0x00")
print("  17: FINE_TUNE  = 0x80")
print()

print("Wavsynth-specific fields (18-22):")
print("  18: SHAPE      = 0x{:02X} ({:3d})".format(inst._data[18], inst._data[18]))
print("  19: SIZE       = 0x{:02X} ({:3d})".format(inst._data[19], inst._data[19]))
print("  20: MULT       = 0x{:02X} ({:3d})".format(inst._data[20], inst._data[20]))
print("  21: WARP       = 0x{:02X} ({:3d})".format(inst._data[21], inst._data[21]))
print("  22: MIRROR     = 0x{:02X} ({:3d}) [SCAN in M8 UI]".format(inst._data[22], inst._data[22]))
print()

print("Filter/Mixer fields (23-32):")
print("  23: FILTER_TYPE = 0x{:02X} ({:3d})".format(inst._data[23], inst._data[23]))
print("  24: CUTOFF      = 0x{:02X} ({:3d})".format(inst._data[24], inst._data[24]))
print("  25: RESONANCE   = 0x{:02X} ({:3d})".format(inst._data[25], inst._data[25]))
print("  26: AMP         = 0x{:02X} ({:3d})".format(inst._data[26], inst._data[26]))
print("  27: LIMIT       = 0x{:02X} ({:3d})".format(inst._data[27], inst._data[27]))
print("  28: PAN         = 0x{:02X} ({:3d})".format(inst._data[28], inst._data[28]))
print("  29: DRY         = 0x{:02X} ({:3d})".format(inst._data[29], inst._data[29]))
print("  30: CHORUS_SEND = 0x{:02X} ({:3d}) [MFX in M8 UI]".format(inst._data[30], inst._data[30]))
print("  31: DELAY_SEND  = 0x{:02X} ({:3d})".format(inst._data[31], inst._data[31]))
print("  32: REVERB_SEND = 0x{:02X} ({:3d})".format(inst._data[32], inst._data[32]))
print()

print("Observation:")
print("  - Wavsynth-specific fields come BEFORE filter/mixer fields")
print("  - This is different from what Rust docs suggested")
print("  - Order: SHAPE, SIZE, MULT, WARP, MIRROR, then filter/mixer")
print()

print("=" * 70)
print("MODULATOR DESTINATIONS")
print("=" * 70)
print()

print("Raw modulator bytes:")
for mod_idx in range(4):
    offset = 63 + (mod_idx * 23)
    print(f"\nModulator {mod_idx} (offset {offset}):")
    print("  Bytes 0-5:", end=" ")
    for i in range(6):
        print(f"0x{inst._data[offset + i]:02X}", end=" ")
    print()

    # Using the modulators property
    mod = inst.modulators[mod_idx]
    print(f"  Via property: type={mod.mod_type}, dest={mod.destination}")

print()
print("Expected destinations (from user):")
print("  Mod 0: 0x01 (VOLUME)")
print("  Mod 1: 0x04 (MULT)")
print("  Mod 2: 0x02 (PITCH)")
print("  Mod 3: 0x05 (WARP)")
print()
