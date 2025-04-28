## WAV Tool Refactoring (22/04/2025)

- Removed defunct WAV processing tools from devtools directory:
  - read_wav_slices.py - This functionality is now handled by the m8.tools.extract_slices module
  - show_wav_structure.py - No longer needed as WAV slice extraction is formally part of the m8.tools package

# Historical Notes

## SLI FX Value Fix (13/04/2025)

Fixed the SLI (slice) FX enum value in m8/enums/sampler.py to use the correct value of 0xA6 (previously was incorrectly set to 0x92). All tests pass with this update.

## Modulator Parameter Summary (04/12/2025)

A critical bug in modulator parameter handling caused specific parameters (like decay) to be lost during binary serialization/deserialization. This especially affected the 303-style acid sound design, which relies heavily on envelope decay parameters.

The problem stemmed from how parameter offsets were mapped to binary positions:
- In the format_config.yaml, the decay parameter has offset 4
- When accounting for the common fields, this would place it at position 6 (2+4) in the buffer
- But the modulator block size is only 6 bytes (positions 0-5), causing these values to be truncated
- When writing, parameters were copied sequentially rather than to their configured positions
- When reading, the parameters couldn't be found at their expected positions

The fix implemented a direct parameter writing/reading approach:
- Modified M8Modulator.write() to write each parameter directly to its configured offset position
- Updated M8Modulator.read() to read each parameter directly from its offset position
- Added bounds checking to ensure values are only written within the block size
- Maintained compatibility with the existing format_config.yaml

This solution ensures all modulator parameters (including important decay values for envelopes) are correctly preserved during binary serialization/deserialization, regardless of their offset values.

## Modulator Parameter Fixed (04/12/2025)

Fixed the critical bug in modulator parameter handling that was causing certain parameters (like decay) to be lost during binary serialization/deserialization.

Original issue:
- When writing modulators to binary format, the M8Modulator.write method incorrectly copied parameter data from M8ModulatorParams.write() to the final binary buffer.
- It treated the params_data as a continuous array starting from index 0, ignoring the actual parameter offsets defined in the configuration.
- In AHD_ENVELOPE, the decay parameter has offset 4 in the configuration, which would place it at position 6 (2+4) in the binary data.
- But with the block size of 6 bytes, this position was outside the valid range.

Solution implemented:
- Modified M8Modulator.write() to write parameters directly to their correct offset positions in the binary buffer.
- Updated M8Modulator.read() to read parameters directly from their offset positions in the binary data.
- This ensures that all parameters are correctly preserved during binary serialization/deserialization, regardless of their offset values.

The fix maintains the existing format_config.yaml parameter definitions while ensuring correct binary representation of all modulator parameters.

## Modulator Parameter Writing Bug (04/12/2025)

Identified a critical bug in the M8Modulator.write method that affects all modulator parameters with non-zero offsets.

Problem: When writing modulators to binary format, the M8Modulator.write method incorrectly copies parameter data from M8ModulatorParams.write() to the final binary buffer. It treats the params_data as a continuous array starting from index 0, ignoring the actual parameter offsets defined in the configuration.

Example:
- In AHD_ENVELOPE, the decay parameter has offset 4 in the configuration
- M8ModulatorParams.write() correctly writes the decay value to offset 4 in its output
- But M8Modulator.write() copies the bytes sequentially, causing the decay value to be written to the wrong position in the final binary
- When reading back, the decay parameter appears as 0x00 instead of the set value

Solution required: Modify M8Modulator.write() to respect parameter offsets when combining modulator parameter data with the common fields (type, destination, amount).

## Instrument Counter Reset Feature (04/09/2025)

Added a reset_instrument_counter() function to address the issue with the global instrument counter being incremented during module import. The counter is used to auto-generate instrument names and should start at 0 for the first instrument created.

Problem: The _INSTRUMENT_COUNTER global variable in m8/api/instruments/__init__.py was initialized at module load time, but could be incremented before any instruments were actually created, causing the first instrument to have a non-zero counter value.

Solution: Added a reset_instrument_counter() function that clients can call before creating their first instrument to ensure the counter starts at 0.

Usage:
```python
from m8.api.instruments import reset_instrument_counter, M8Instrument

# Reset counter to ensure the first instrument starts with 0000
reset_instrument_counter()

# Create instruments
instr1 = M8Instrument(instrument_type="WAVSYNTH")  # Will have "WAVSYNTH0000" name
instr2 = M8Instrument(instrument_type="FMSYNTH")   # Will have "FMSYNTH0001" name
```

This file has been migrated to the more comprehensive ARCHITECTURE.md document.

Please refer to ARCHITECTURE.md for current technical documentation.