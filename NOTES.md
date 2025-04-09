# Historical Notes

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