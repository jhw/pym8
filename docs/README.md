# pym8 Documentation

This directory contains documentation for the pym8 M8 file format library.

## Documentation Files

### [FX.md](FX.md)
Complete reference of all M8 FX command codes for phrase steps.
- Sequence commands (global FX like retrigger, groove, etc.)
- Instrument commands (sampler-specific FX like playback mode, filter, etc.)
- Usage examples with code

### [SAMPLER.md](SAMPLER.md)
Byte-level reference for M8 Sampler instrument parameters.
- Complete parameter offset table
- Playback, filter, and mixer parameters
- Send effects (chorus, delay, reverb)
- Usage examples with code

## Quick Reference

### Setting Phrase FX

```python
from m8.api.phrase import M8PhraseStep
from m8.api.fx import M8FXTuple

step = M8PhraseStep(note=0x24, velocity=0x6F, instrument=0x00)
step.fx[0] = M8FXTuple(key=0x08, value=0x40)  # RET (retrigger)
step.fx[1] = M8FXTuple(key=0x86, value=0xC0)  # LEN (cut)
```

### Setting Instrument Parameters

```python
from m8.api.sampler import M8Sampler

sampler = M8Sampler(name="KICK", sample_path="samples/kick.wav")
sampler.set(32, 0x80)  # Set delay send
sampler.set(33, 0x40)  # Set reverb send
```

## External References

The M8 file format documentation in this repository is based on these excellent open-source projects:

### Primary References

- **[m8-file-parser](https://github.com/Twinside/m8-file-parser)** (Rust)
  The most complete and up-to-date M8 file format parser. This is the authoritative source for:
  - Binary structure layouts
  - FX command codes
  - Instrument parameter offsets
  - Version-specific format changes (firmware 4.0 - 6.2+)

- **[m8-js](https://github.com/whitlockjc/m8-js)** (JavaScript)
  JavaScript implementation with good documentation of the M8 format.

- **[m8-files](https://github.com/AlexCharlton/m8-files)** (Rust)
  Original Rust parser that inspired m8-file-parser.

### Official M8 Resources

- **[Dirtywave M8 Tracker](https://dirtywave.com/products/m8-tracker)**
  Official M8 hardware synthesizer and tracker

- **[M8 Headless](https://github.com/Dirtywave/M8Headless)**
  Official headless M8 firmware for running on Teensy hardware

## Contributing

When adding new documentation:

1. **Verify against m8-file-parser**: Always cross-reference the [Rust parser](https://github.com/Twinside/m8-file-parser) to ensure accuracy
2. **Include examples**: Show practical Python code examples
3. **Document firmware versions**: Note if features are version-specific
4. **Keep tables organized**: Use consistent formatting for parameter tables
5. **Link references**: Cross-link between related documentation files

## File Format Versions

The pym8 library currently targets M8 firmware version **6.2+**. Key changes across versions:

- **V2**: Initial format (23 sequence commands, 36 mixer commands)
- **V3**: Added RND, RNL, RMX, PBN, TBX, OFF commands (27 sequence commands)
- **V4**: Expanded mixer commands to 45
- **V6.2**: Latest format with 50 mixer commands (XRH, XMT, OTT, OTC, OTI added)

See the [m8-file-parser version history](https://github.com/Twinside/m8-file-parser/blob/master/src/fx.rs) for complete version details.

## Byte Order and Data Types

All M8 data uses:
- **Little-endian byte order** for multi-byte values
- **Unsigned 8-bit integers** (0x00-0xFF) for most parameters
- **Null-terminated strings** for text fields (name, sample path)
- **Float32** for tempo (4 bytes, little-endian)

## Getting Help

- **Issues**: [GitHub Issues](https://github.com/jhw/pym8/issues)
- **Examples**: See `demos/` directory for working code examples
- **Tests**: Check `tests/` directory for API usage examples
