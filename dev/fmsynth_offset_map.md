# FM Synth Parameter Offset Map

Based on reverse engineering tmp/FM-DEMO.m8s instrument 0x00.

## Common Parameters (0x00-0x12)

| Offset | Size | Name | Value | Description |
|--------|------|------|-------|-------------|
| 0x00 | 1 | TYPE | 0x04 | Instrument type (FMSYNTH) |
| 0x01-0x0C | 12 | NAME | - | Instrument name (12 bytes, null-padded) |
| 0x0D | 1 | TRANSPOSE | 0x01 | Pitch transpose |
| 0x0E | 1 | TABLE_TICK | 0x01 | Table tick rate |
| 0x0F | 1 | VOLUME | 0x00 | Master volume |
| 0x10 | 1 | PITCH | 0x00 | Pitch offset |
| 0x11 | 1 | FINE_TUNE | 0x80 | Fine pitch (0x80 = center) |
| 0x12 | 1 | ALGO | 0x0B | FM algorithm (0x00-0x0B) |

## Operator Parameters (0x13-0x2E)

The structure appears to be organized by parameter type, not by operator:

| Offset | Size | Name | Values | Description |
|--------|------|------|--------|-------------|
| 0x13-0x16 | 4 | OP_SHAPE_ABCD | 00 01 02 03 | Operator shapes (FMWave enum) |
| 0x17-0x1E | 8 | OP_DATA_1 | 01 19 02 32 03 4B 04 00 | Interleaved data (need to decode) |
| 0x1F-0x26 | 8 | LEV_FB_ABCD | 10 20 30 40 50 60 70 80 | Level/Feedback pairs (A-lev, A-fb, B-lev, B-fb, ...) |
| 0x27-0x2A | 4 | MOD_DEST_1234 | 01 06 0B 10 | Modulation destinations? |
| 0x2B-0x2E | 4 | UNKNOWN_1 | 00 00 00 00 | Unknown |

### Ratio Values (Extracted from 0x17-0x1E)

Looking at every other byte starting at 0x18:
- 0x18: 0x19 = 25 decimal (Operator A ratio)
- 0x1A: 0x32 = 50 decimal (Operator B ratio)
- 0x1C: 0x4B = 75 decimal (Operator C ratio) - user said 70
- 0x1E: 0x00 = 0 decimal (Operator D ratio)

Odd bytes (0x17, 0x19, 0x1B, 0x1D) contain: 01 02 03 04 (possibly operator indices or ratio_fine)

## Modulator Parameters (0x2F-0x32)

| Offset | Size | Name | Values | Description |
|--------|------|------|--------|-------------|
| 0x2F-0x32 | 4 | MOD_VALUES_1234 | 40 50 60 50 | Modulator values (user said: 40 50 60 50) |

## Filter & Mixer Parameters (0x33-0x3C)

| Offset | Size | Name | Value | Description |
|--------|------|------|-------|-------------|
| 0x33 | 1 | FILTER_TYPE | 0x07 | Filter type |
| 0x34 | 1 | CUTOFF | 0xB0 | Filter cutoff frequency |
| 0x35 | 1 | RESONANCE | 0xC0 | Filter resonance |
| 0x36 | 1 | AMP | 0x10 | Amplifier level |
| 0x37 | 1 | LIMIT | 0x04 | Limiter type/amount |
| 0x38 | 1 | PAN | 0x80 | Stereo pan (0x80 = center) |
| 0x39 | 1 | DRY | 0xC0 | Dry/wet mix |
| 0x3A | 1 | CHORUS_SEND | 0x90 | Chorus send level |
| 0x3B | 1 | DELAY_SEND | 0x40 | Delay send level |
| 0x3C | 1 | REVERB_SEND | 0xB0 | Reverb send level |

## Modulators (0x3D onwards)

Standard M8 modulator structure starts at offset 0x3D (61 decimal).
Each modulator is 30 bytes (same as other instruments).

Total: 4 modulators × 30 bytes = 120 bytes.

## Summary

- Common params: 0x00-0x12 (19 bytes)
- FM-specific params: 0x13-0x3C (42 bytes)
- Modulators: 0x3D-0xF4 (120 bytes)
- Total: 181 bytes before any additional data

## FM-Specific Enums

### FMAlgo (0x00-0x0B)
From m8-file-parser Rust code:
- 0x00: "A>B>C>D"
- 0x01: "[A+B]>C>D"
- 0x02: "[A>B+C]>D"
- 0x03: "[A>B+A>C]>D"
- 0x04: "[A+B+C]>D"
- 0x05: "[A>B>C]+D"
- 0x06: "[A>B>C]+[A>B>D]"
- 0x07: "[A>B]+[C>D]"
- 0x08: "[A>B]+[A>C]+[A>D]"
- 0x09: "[A>B]+[A>C]+D"
- 0x0A: "[A>B]+C+D"
- 0x0B: "A+B+C+D"

### FMWave (Operator Shapes)
From Rust code (0x00-0x45):
- 0x00: SIN
- 0x01: SW2 (half sine)
- 0x02: SW3 (third sine)
- 0x03: SW4 (quarter sine)
- 0x04: SW5
- 0x05: SW6
- 0x06: TRI
- 0x07: SAW
- 0x08: SQR
- 0x09: PUL
- 0x0A: IMP
- 0x0B: NOI
- 0x0C: NLP
- 0x0D: NHP
- 0x0E: NBP
- 0x0F: CLK
- 0x10-0x45: W09-W45 (additional waveforms)

### FMSynthModDest (Modulation Destinations)
From m8-js (0x00-0x0A):
- 0x00: OFF
- 0x01: VOLUME
- 0x02: PITCH
- 0x03: MOD1
- 0x04: MOD2
- 0x05: MOD3
- 0x06: MOD4
- 0x07: CUTOFF
- 0x08: RES
- 0x09: AMP
- 0x0A: PAN

Additional from Rust DESTINATIONS array (0x0B-0x0E):
- 0x0B: MOD_AMT
- 0x0C: MOD_RATE
- 0x0D: MOD_BOTH
- 0x0E: MOD_BINV
