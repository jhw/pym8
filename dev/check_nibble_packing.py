#!/usr/bin/env python3
"""Check if bytes 13-14 form a nibble-packed structure."""

from pathlib import Path

print("Checking if bytes 13-14 form a nibble-packed structure:")
print("=" * 70)
print()

for file in sorted(Path('tmp/dw01-synthdrums/m8i').glob('*.m8i'))[:10]:
    with open(file, 'rb') as f:
        data = f.read(20)

    name = file.stem
    byte12 = data[12]
    byte13 = data[13]
    byte14 = data[14]

    # Extract nibbles
    byte13_high = (byte13 >> 4) & 0x0F
    byte13_low = byte13 & 0x0F
    byte14_high = (byte14 >> 4) & 0x0F
    byte14_low = byte14 & 0x0F

    print(f"{name:15s}")
    print(f"  Byte 12: 0x{byte12:02X} = {byte12:3d}")
    print(f"  Byte 13: 0x{byte13:02X} = {byte13:3d}  (high={byte13_high:X}, low={byte13_low:X})")
    print(f"  Byte 14: 0x{byte14:02X} = {byte14:3d}  (high={byte14_high:X}, low={byte14_low:X})")

    # Check if byte 13 high nibble is always 0x1
    if byte13_high == 0x1:
        print(f"  → Byte 13 high nibble = 0x1 (format marker?)")

    print()

print()
print("Pattern analysis:")
print("  - Byte 13 = 0x10 consistently (high=0x1, low=0x0)")
print("  - Byte 14 = 0x04 (FM Synth type)")
print()
print("If nibble-packed like modulators:")
print(f"  join_nibbles(0x0, 0x4) = {(0x0 << 4) | 0x4:02X} = {(0x0 << 4) | 0x4} ✓ (matches type 4!)")
print()
print("This suggests:")
print("  - Byte 13 high nibble (0x1) = M8i format marker")
print("  - Byte 13 low nibble (0x0) + Byte 14 (0x4) = instrument type (nibble-packed)")
print()
print("If true, header would be 13 bytes, with instrument starting at byte 13!")
