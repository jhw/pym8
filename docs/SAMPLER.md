# M8 Sampler Instrument

This document describes the byte offsets for M8 Sampler instrument parameters.

Sampler parameters are accessed using the low-level `get()` and `set()` methods:

```python
from m8.api.sampler import M8Sampler

sampler = M8Sampler(name="KICK", sample_path="samples/kick.wav")

# Get parameter value
value = sampler.get(32)  # Get delay send

# Set parameter value
sampler.set(32, 0x80)    # Set delay send to 0x80
```

## Instrument Structure

The M8 Sampler instrument uses a 215-byte binary structure with the following layout:

### Common Parameters (Offsets 0-12)

| Offset | Parameter | Type | Default | Description |
|--------|-----------|------|---------|-------------|
| 0 | Type | byte | 0x02 | Instrument type (2 = Sampler) |
| 1-12 | Name | string | "" | Instrument name (12 bytes) |

### Playback Parameters (Offsets 13-23)

| Offset | Parameter | Type | Default | Range | Description |
|--------|-----------|------|---------|-------|-------------|
| 13 | Transpose | byte | 0x00 | 0x00-0xFF | Pitch transpose |
| 14 | Table Tick | byte | 0x00 | 0x00-0xFF | Table tick rate |
| 15 | Volume | byte | 0x00 | 0x00-0xFF | Master volume |
| 16 | Pitch | byte | 0x00 | 0x00-0xFF | Pitch offset |
| 17 | Fine Tune | byte | 0x80 | 0x00-0xFF | Fine pitch adjustment (0x80 = center) |
| 18 | Play Mode | byte | 0x00 | 0x00-0x08 | Sample playback mode |
| 19 | Slice | byte | 0x00 | 0x00-0xFF | Slice selection |
| 20 | Start | byte | 0x00 | 0x00-0xFF | Sample start position |
| 21 | Loop Start | byte | 0x00 | 0x00-0xFF | Loop start position |
| 22 | Length | byte | 0xFF | 0x00-0xFF | Sample length (0xFF = full) |
| 23 | Degrade | byte | 0x00 | 0x00-0xFF | Bitcrusher amount |

### Play Modes (Offset 18)

| Value | Mode | Description |
|-------|------|-------------|
| 0x00 | FWD | Forward |
| 0x01 | REV | Reverse |
| 0x02 | FWDLOOP | Forward loop |
| 0x03 | REVLOOP | Reverse loop |
| 0x04 | FWD_PP | Forward ping-pong |
| 0x05 | REV_PP | Reverse ping-pong |
| 0x06 | OSC | Oscillator |
| 0x07 | OSC_REV | Oscillator reverse |
| 0x08 | OSC_PP | Oscillator ping-pong |

### Filter Parameters (Offsets 24-26)

| Offset | Parameter | Type | Default | Range | Description |
|--------|-----------|------|---------|-------|-------------|
| 24 | Filter Type | byte | 0x00 | 0x00-0xFF | Filter type selection |
| 25 | Cutoff | byte | 0xFF | 0x00-0xFF | Filter cutoff frequency (0xFF = open) |
| 26 | Resonance | byte | 0x00 | 0x00-0xFF | Filter resonance |

### Mixer Parameters (Offsets 27-33)

| Offset | Parameter | Type | Default | Range | Description |
|--------|-----------|------|---------|-------|-------------|
| 27 | Amp | byte | 0x00 | 0x00-0xFF | Amplifier level |
| 28 | Limit | byte | 0x00 | 0x00-0xFF | Limiter amount |
| 29 | Pan | byte | 0x80 | 0x00-0xFF | Stereo pan (0x80 = center) |
| 30 | Dry | byte | 0xC0 | 0x00-0xFF | Dry/wet mix level |
| 31 | Chorus Send | byte | 0x00 | 0x00-0xFF | Send to chorus effect |
| 32 | Delay Send | byte | 0x00 | 0x00-0xFF | Send to delay effect |
| 33 | Reverb Send | byte | 0x00 | 0x00-0xFF | Send to reverb effect |

### Modulators (Offsets 63-118)

| Offset | Parameter | Description |
|--------|-----------|-------------|
| 63-77 | Modulator 1 | AHD envelope (15 bytes) |
| 78-92 | Modulator 2 | AHD envelope (15 bytes) |
| 93-107 | Modulator 3 | LFO (15 bytes) |
| 108-122 | Modulator 4 | LFO (15 bytes) |

See [MODULATORS.md](MODULATORS.md) for detailed modulator structure.

### Sample Path (Offsets 87-214)

| Offset | Parameter | Type | Default | Description |
|--------|-----------|------|---------|-------------|
| 87-214 | Sample Path | string | "" | Relative path to sample file (128 bytes) |

## Usage Examples

### Basic Sampler Setup

```python
from m8.api.sampler import M8Sampler

# Create sampler with sample
sampler = M8Sampler(
    name="KICK",
    sample_path="samples/kick.wav"
)

# Set basic parameters
sampler.set(15, 0xC0)  # Volume to 0xC0
sampler.set(17, 0x80)  # Fine tune to center (0x80)
sampler.set(22, 0xFF)  # Full length
```

### Setting Send Effects

```python
# Set chorus send
sampler.set(31, 0x80)  # Chorus to 0x80 (medium)

# Set delay send
sampler.set(32, 0xC0)  # Delay to 0xC0 (high)

# Set reverb send
sampler.set(33, 0x40)  # Reverb to 0x40 (low)
```

### Filter Configuration

```python
# Set up a low-pass filter
sampler.set(24, 0x00)  # Filter type (0x00 = low-pass)
sampler.set(25, 0x80)  # Cutoff to 0x80 (medium)
sampler.set(26, 0x40)  # Resonance to 0x40
```

### Playback Mode

```python
# Set reverse playback
sampler.set(18, 0x01)  # Play mode = REV

# Set forward loop
sampler.set(18, 0x02)  # Play mode = FWDLOOP
sampler.set(21, 0x20)  # Loop start at 0x20
```

### Advanced: Slice and Start Position

```python
# Configure sample slicing
sampler.set(19, 0x08)  # Select slice 8
sampler.set(20, 0x00)  # Start at beginning
sampler.set(22, 0x80)  # Length to half
```

## Property Access

For common parameters, you can also use the higher-level properties:

```python
# Name property
sampler.name = "KICK"
print(sampler.name)  # "KICK"

# Sample path property
sampler.sample_path = "samples/kick.wav"
print(sampler.sample_path)  # "samples/kick.wav"
```

## Notes

- All byte values are in range 0x00-0xFF (0-255)
- Default values marked with non-zero values are automatically applied on initialization
- Pan and fine tune use 0x80 (128) as center position
- Length 0xFF = full sample length
- Send effects (chorus/delay/reverb) default to 0x00 (off)
- The instrument binary structure is 215 bytes total

## References

- [m8-file-parser (Rust)](https://github.com/Twinside/m8-file-parser/blob/master/src/instruments/sampler.rs) - Sampler instrument specification
- [FX.md](FX.md) - Phrase-level FX commands
