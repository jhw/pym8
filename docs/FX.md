# M8 FX Commands

This document lists all FX command codes for use in M8 phrase steps.

FX commands are set on phrase steps using the `M8FXTuple` class:

```python
from m8.api.fx import M8FXTuple

# Example: Add retrigger effect
step.fx[0] = M8FXTuple(key=0x08, value=0x40)
```

## Sequence Commands (Global FX)

These commands work across all instrument types and affect playback behavior.

| Code | Command | Description |
|------|---------|-------------|
| 0x00 | ARP | Arpeggio |
| 0x01 | CHA | Chord (arpeggio variation) |
| 0x02 | DEL | Delay (phrase) |
| 0x03 | GRV | Groove |
| 0x04 | HOP | Jump to step |
| 0x05 | KIL | Kill/stop note |
| 0x06 | RND | Random |
| 0x07 | RNL | Random (limited) |
| 0x08 | RET | Retrigger |
| 0x09 | REP | Repeat |
| 0x0A | RMX | Remix (randomize) |
| 0x0B | NTH | N-th (conditional) |
| 0x0C | PSL | Pan slide left |
| 0x0D | PBN | Probability note |
| 0x0E | PVB | Pitch vibrato |
| 0x0F | PVX | Pitch vibrato extended |
| 0x10 | SCA | Scale |
| 0x11 | SCG | Scale (global) |
| 0x12 | SED | Set delay |
| 0x13 | SNG | Song |
| 0x14 | TBL | Table |
| 0x15 | THO | Tempo hop |
| 0x16 | TIC | Tick |
| 0x17 | TBX | Table extended |
| 0x18 | TPO | Tempo |
| 0x19 | TSP | Transpose |
| 0x1A | OFF | Note off |

## Instrument Commands (Sampler)

These commands are specific to sampler instruments and control playback parameters.

| Code | Command | Description |
|------|---------|-------------|
| 0x80 | VOL | Volume |
| 0x81 | PIT | Pitch |
| 0x82 | FIN | Fine tune |
| 0x83 | PLY | Play mode (0x00=FWD, 0x01=REV) |
| 0x84 | STA | Start position |
| 0x85 | LOP | Loop start |
| 0x86 | LEN | Length/cut |
| 0x87 | DEG | Degrade |
| 0x88 | FLT | Filter type |
| 0x89 | CUT | Cutoff frequency |
| 0x8A | RES | Resonance |
| 0x8B | AMP | Amplifier |
| 0x8C | LIM | Limiter |
| 0x8D | PAN | Pan |
| 0x8E | DRY | Dry/wet mix |
| 0x8F | SCH | Send chorus |
| 0x90 | SDL | Send delay |
| 0x91 | SRV | Send reverb |

## Common Usage Examples

```python
from m8.api.phrase import M8Phrase, M8PhraseStep
from m8.api.fx import M8FXTuple

phrase = M8Phrase()

# Add retrigger effect
step = M8PhraseStep(note=0x24, velocity=0x6F, instrument=0x00)
step.fx[0] = M8FXTuple(key=0x08, value=0x40)  # RET with value 0x40
phrase[0] = step

# Add reverse play effect
step = M8PhraseStep(note=0x24, velocity=0x6F, instrument=0x00)
step.fx[0] = M8FXTuple(key=0x83, value=0x01)  # PLY reverse
phrase[4] = step

# Add length cut effect
step = M8PhraseStep(note=0x24, velocity=0x6F, instrument=0x00)
step.fx[0] = M8FXTuple(key=0x86, value=0xC0)  # LEN cut to 0xC0
phrase[8] = step

# Multiple FX on one step (up to 3 FX per step)
step = M8PhraseStep(note=0x24, velocity=0x6F, instrument=0x00)
step.fx[0] = M8FXTuple(key=0x08, value=0x40)  # RET
step.fx[1] = M8FXTuple(key=0x86, value=0xC0)  # LEN
phrase[12] = step
```

## Notes

- Each phrase step can have up to **3 FX** (fx[0], fx[1], fx[2])
- Sequence commands (0x00-0x1A) are global and work with all instruments
- Instrument commands (0x80+) are specific to the instrument type
- FX values are typically in the range 0x00-0xFF
- Command codes are based on M8 firmware version 3.0+

## References

- [m8-file-parser (Rust)](https://github.com/Twinside/m8-file-parser) - Complete M8 file format specification
- [m8-js](https://github.com/whitlockjc/m8-js) - JavaScript M8 file parser
