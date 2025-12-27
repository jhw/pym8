#!/usr/bin/env python3
"""
Test FM Synth Round-Trip: API vs Raw Binary

This script creates an M8s file with:
- Slot 00: Instrument read via API and written via API (round-trip test)
- Slot 01: Instrument as raw binary copy (reference/ground truth)

Load the resulting M8s on your M8 device and toggle between slots 00 and 01
to verify if they match. If they don't match, the API read/write is corrupting data.

Usage:
    python dev/test_fm_roundtrip.py [path/to/instrument.m8i]

Default: tmp/dw01-synthdrums/m8i/KICK_MORPH.m8i
"""

import sys
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from m8.api.project import M8Project
from m8.api.instrument import M8Instrument


def test_fm_roundtrip(m8i_path):
    """Test FM synth round-trip by comparing API vs raw binary.

    Args:
        m8i_path: Path to M8i instrument file
    """
    m8i_path = Path(m8i_path)

    if not m8i_path.exists():
        print(f"Error: M8i file not found: {m8i_path}")
        return 1

    print("=" * 70)
    print("FM SYNTH ROUND-TRIP TEST")
    print("=" * 70)
    print()
    print(f"Source M8i: {m8i_path}")
    print()

    # Step 1: Read M8i via API
    print("Step 1: Reading M8i via API...")
    print("-" * 70)
    inst_via_api = M8Instrument.read_from_file(str(m8i_path))
    print(f"  Name: {inst_via_api.name}")
    print(f"  Type: {inst_via_api._data[0]} (should be 4 for FM Synth)")
    print()

    # Log modulators as read by API
    print("  Modulators (as read by API):")
    for i in range(4):
        mod = inst_via_api.modulators[i]
        print(f"    Mod {i}: type={mod.mod_type}, dest={mod.destination}, amount={mod.amount}")
        print(f"           raw bytes: {' '.join(f'{b:02X}' for b in mod._data)}")
    print()

    # Step 2: Read raw M8i binary
    print("Step 2: Reading raw M8i binary...")
    print("-" * 70)
    with open(m8i_path, 'rb') as f:
        m8i_data = f.read()

    # M8i files have 14-byte header, instrument starts at offset 14
    M8I_HEADER_SIZE = 14
    INSTRUMENT_SIZE = 215

    raw_instrument_data = m8i_data[M8I_HEADER_SIZE:M8I_HEADER_SIZE + INSTRUMENT_SIZE]
    print(f"  Extracted {len(raw_instrument_data)} bytes of raw instrument data")
    raw_name = raw_instrument_data[1:13].decode('ascii', errors='ignore').rstrip('\x00')
    print(f"  Name from raw: {raw_name}")
    print()

    # Log modulators from raw binary
    print("  Modulators (from raw binary):")
    # Check both offset 61 and 63 to see which looks correct
    for test_offset in [61, 63]:
        print(f"\n    Testing offset {test_offset}:")
        for i in range(4):
            mod_start = test_offset + (i * 6)
            mod_bytes = raw_instrument_data[mod_start:mod_start + 6]
            type_dest = mod_bytes[0]
            mod_type = (type_dest >> 4) & 0x0F
            mod_dest = type_dest & 0x0F
            amount = mod_bytes[1]
            print(f"      Mod {i}: type={mod_type}, dest={mod_dest}, amount={amount}")
            print(f"             raw bytes: {' '.join(f'{b:02X}' for b in mod_bytes)}")
    print()

    # Step 3: Create M8s project
    print("Step 3: Creating M8s project...")
    print("-" * 70)
    project = M8Project.initialise()
    project.metadata.name = "FM-TEST"
    print("  Created new project: FM-TEST")
    print()

    # Step 4: Write instrument to slot 00 via API (round-trip)
    print("Step 4: Writing to slot 00 via API (round-trip test)...")
    print("-" * 70)
    project.instruments[0] = inst_via_api
    print(f"  Slot 00: {inst_via_api.name} (via API)")

    # Get what will be written
    slot00_data = inst_via_api.write()
    print(f"  Will write {len(slot00_data)} bytes")
    print()
    print("  Modulators (as will be written to slot 00):")

    # Check what offset was used for writing
    from m8.api.instruments.fmsynth import M8FMSynth
    mod_offset = getattr(M8FMSynth, 'MODULATORS_OFFSET', 63) if isinstance(inst_via_api, M8FMSynth) else 63
    print(f"  Using MODULATORS_OFFSET: {mod_offset}")
    print()

    for i in range(4):
        mod_start = mod_offset + (i * 6)
        mod_bytes = slot00_data[mod_start:mod_start + 6]
        type_dest = mod_bytes[0]
        mod_type = (type_dest >> 4) & 0x0F
        mod_dest = type_dest & 0x0F
        amount = mod_bytes[1]
        print(f"    Mod {i}: type={mod_type}, dest={mod_dest}, amount={amount}")
        print(f"           raw bytes: {' '.join(f'{b:02X}' for b in mod_bytes)}")
    print()

    # Step 5: Write raw binary directly to slot 01 (reference)
    print("Step 5: Writing raw binary to slot 01 (reference/ground truth)...")
    print("-" * 70)

    # Create a minimal instrument wrapper with raw data
    class RawInstrument:
        def __init__(self, raw_data):
            self._data = bytearray(raw_data)
            from m8.api.version import M8Version
            self.version = M8Version()
            # Don't read modulators - keep raw

        def write(self):
            return bytes(self._data)

    raw_inst = RawInstrument(raw_instrument_data)
    project.instruments[1] = raw_inst
    print(f"  Slot 01: RAW BINARY (ground truth)")
    print()

    # Step 6: Save M8s file
    output_path = Path("tmp/FM-ROUNDTRIP-TEST.m8s")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    print(f"Step 6: Saving M8s file...")
    print("-" * 70)
    project.write_to_file(str(output_path))
    print(f"  Saved: {output_path}")
    print()

    # Step 7: Verification summary
    print("=" * 70)
    print("VERIFICATION INSTRUCTIONS")
    print("=" * 70)
    print()
    print("1. Copy this file to your M8 device:")
    print(f"   {output_path}")
    print()
    print("2. Load FM-ROUNDTRIP-TEST.m8s on your M8")
    print()
    print("3. Navigate to INSTRUMENT screen")
    print()
    print("4. Compare slot 00 vs slot 01:")
    print("   - Slot 00: API round-trip (may have bugs)")
    print("   - Slot 01: Raw binary (correct reference)")
    print()
    print("5. Toggle between them and check:")
    print("   - Do all parameters match?")
    print("   - Do all 4 modulators match?")
    print("   - Specifically check modulator 0:")
    print("     * Should have dest=VOLUME (or whatever the source has)")
    print("     * Check attack/hold/decay values")
    print()
    print("If they DON'T match, our API has a bug!")
    print("=" * 70)

    return 0


if __name__ == '__main__':
    # Default to KICK_MORPH
    default_m8i = Path("tmp/dw01-synthdrums/m8i/KICK_MORPH.m8i")

    if len(sys.argv) > 1:
        m8i_path = Path(sys.argv[1])
    else:
        m8i_path = default_m8i
        print(f"Using default M8i: {m8i_path}")
        print()

    sys.exit(test_fm_roundtrip(m8i_path))
