#!/usr/bin/env python
"""Final verification: read plasticant.m8s and verify all parameters."""

from m8.api.project import M8Project
from m8.api.instruments.wavsynth import M8WavsynthParam

# Load the test file
project = M8Project.read_from_file('tmp/plasticant.m8s')
inst = project.instruments[0]

print("=" * 70)
print("FINAL VERIFICATION - PLASTICANT.M8S")
print("=" * 70)
print()

# Test reading via enum
print("Reading parameters via M8WavsynthParam enum:")
params = {
    'SHAPE': (M8WavsynthParam.SHAPE, 0x09),
    'SIZE': (M8WavsynthParam.SIZE, 0x0A),
    'MULT': (M8WavsynthParam.MULT, 0x0B),
    'WARP': (M8WavsynthParam.WARP, 0x0C),
    'MIRROR': (M8WavsynthParam.MIRROR, 0x0D),
    'FILTER_TYPE': (M8WavsynthParam.FILTER_TYPE, 0x0A),
    'CUTOFF': (M8WavsynthParam.CUTOFF, 0x0E),
    'RESONANCE': (M8WavsynthParam.RESONANCE, 0x0F),
    'AMP': (M8WavsynthParam.AMP, 0x10),
    'LIMIT': (M8WavsynthParam.LIMIT, 0x07),
    'PAN': (M8WavsynthParam.PAN, 0x11),
    'DRY': (M8WavsynthParam.DRY, 0x12),
    'CHORUS_SEND': (M8WavsynthParam.CHORUS_SEND, 0x13),
    'DELAY_SEND': (M8WavsynthParam.DELAY_SEND, 0x14),
    'REVERB_SEND': (M8WavsynthParam.REVERB_SEND, 0x15),
}

all_correct = True

for name, (enum_offset, expected_val) in params.items():
    actual_val = inst.get(enum_offset)
    match = "✓" if actual_val == expected_val else "✗"
    if actual_val != expected_val:
        all_correct = False
    print(f"  {name:15s} = 0x{actual_val:02X} (expected 0x{expected_val:02X}) {match}")

print()
print("Modulator destinations:")
expected_dests = [0x01, 0x04, 0x02, 0x05]
dest_names = ['VOLUME', 'MULT', 'PITCH', 'WARP']

for i in range(4):
    actual_dest = inst.modulators[i].destination
    expected_dest = expected_dests[i]
    match = "✓" if actual_dest == expected_dest else "✗"
    if actual_dest != expected_dest:
        all_correct = False
    print(f"  Mod {i}: dest=0x{actual_dest:02X} (expected 0x{expected_dest:02X} {dest_names[i]}) {match}")

print()
if all_correct:
    print("✅ ALL VERIFICATIONS PASSED!")
    print("   The wavsynth parameter offsets are now correct.")
else:
    print("❌ SOME VERIFICATIONS FAILED!")
    print("   Please review the offset mappings.")
