# pym8

A Python library for reading and writing DirtyWave M8 tracker files.

## Overview

pym8 is a Python package for programmatically creating, reading, and manipulating M8 project files (.m8s). The M8 is a portable music tracker and synthesizer by [Dirtywave](https://dirtywave.com/products/m8-tracker).

This library provides a high-level API for working with M8 projects, including:
- Creating and modifying instruments (samplers)
- Building phrases with notes and FX commands
- Arranging chains and song sequences
- Reading and writing .m8s project files

## Installation

```bash
pip install -e .
```

Or for development:

```bash
pip install -r requirements-dev.txt
```

## Quick Start

### Creating a Simple Project

```python
from m8.api.project import M8Project
from m8.api.sampler import M8Sampler, M8SamplerParam
from m8.api.phrase import M8Phrase, M8PhraseStep
from m8.api.chain import M8Chain, M8ChainStep
from m8.api.fx import M8FXTuple, M8SequenceFX, M8SamplerFX

# Initialize a new project from template
project = M8Project.initialise()
project.metadata.name = "MY-SONG"
project.metadata.tempo = 140

# Create a sampler instrument
kick = M8Sampler(name="KICK", sample_path="samples/kick.wav")
kick.set(M8SamplerParam.DELAY_SEND, 0x80)  # Add delay send
project.instruments[0] = kick

# Create a phrase with beats
phrase = M8Phrase()
for step in [0, 4, 8, 12]:  # Four-on-the-floor
    phrase[step] = M8PhraseStep(
        note=0x24,      # C-4
        velocity=0x6F,  # Full velocity
        instrument=0x00 # Use instrument slot 0
    )

project.phrases[0] = phrase

# Create a chain referencing the phrase
chain = M8Chain()
chain[0] = M8ChainStep(phrase=0x00, transpose=0x00)
project.chains[0] = chain

# Add chain to song
project.song[0][0] = 0x00  # Chain 0 at row 0, track 0

# Save project
project.write_to_file("MY-SONG.m8s")
```

### Reading an Existing Project

```python
from m8.api.project import M8Project

# Read project from file
project = M8Project.read_from_file("existing-song.m8s")

# Access project data
print(f"Project: {project.metadata.name}")
print(f"Tempo: {project.metadata.tempo}")

# Inspect instruments
for i, instrument in enumerate(project.instruments):
    if instrument and hasattr(instrument, 'name'):
        print(f"Instrument {i}: {instrument.name}")
```

## Features

### Instruments

Currently supports M8 Sampler instruments with full parameter control:

```python
from m8.api.sampler import M8Sampler, M8SamplerParam, M8PlayMode

sampler = M8Sampler(name="SNARE", sample_path="samples/snare.wav")

# Set playback parameters
sampler.set(M8SamplerParam.VOLUME, 0xFF)
sampler.set(M8SamplerParam.PLAY_MODE, M8PlayMode.FWDLOOP)
sampler.set(M8SamplerParam.START, 0x00)
sampler.set(M8SamplerParam.LENGTH, 0xFF)

# Set filter parameters
sampler.set(M8SamplerParam.FILTER_TYPE, 0x01)  # LP filter
sampler.set(M8SamplerParam.CUTOFF, 0xC0)
sampler.set(M8SamplerParam.RESONANCE, 0x40)

# Set mixer/sends
sampler.set(M8SamplerParam.PAN, 0x80)  # Center
sampler.set(M8SamplerParam.CHORUS_SEND, 0x40)
sampler.set(M8SamplerParam.DELAY_SEND, 0x80)
sampler.set(M8SamplerParam.REVERB_SEND, 0x60)
```

### Phrases and FX Commands

Create phrases with notes and apply FX commands using typed enums:

```python
from m8.api.phrase import M8Phrase, M8PhraseStep
from m8.api.fx import M8FXTuple, M8SequenceFX, M8SamplerFX

phrase = M8Phrase()

# Add a note with retrigger FX
step = M8PhraseStep(note=0x30, velocity=0x6F, instrument=0x00)
step.fx[0] = M8FXTuple(key=M8SequenceFX.RET, value=0x40)  # Retrigger
step.fx[1] = M8FXTuple(key=M8SamplerFX.LEN, value=0xC0)   # Sample length
phrase[0] = step

# Common sequence FX
step.fx[0] = M8FXTuple(key=M8SequenceFX.ARP, value=0x03)  # Arpeggio
step.fx[0] = M8FXTuple(key=M8SequenceFX.HOP, value=0x08)  # Jump to step 8
step.fx[0] = M8FXTuple(key=M8SequenceFX.KIL, value=0x00)  # Kill note

# Common sampler FX
step.fx[0] = M8FXTuple(key=M8SamplerFX.VOL, value=0xFF)   # Volume
step.fx[0] = M8FXTuple(key=M8SamplerFX.PIT, value=0x0C)   # Pitch up
step.fx[0] = M8FXTuple(key=M8SamplerFX.PLY, value=0x01)   # Reverse playback
step.fx[0] = M8FXTuple(key=M8SamplerFX.CUT, value=0xC0)   # Filter cutoff
```

### Chains and Song Arrangement

```python
from m8.api.chain import M8Chain, M8ChainStep

# Create a chain with multiple phrases
chain = M8Chain()
chain[0] = M8ChainStep(phrase=0x00, transpose=0x00)   # Phrase 0, no transpose
chain[1] = M8ChainStep(phrase=0x01, transpose=0x0C)   # Phrase 1, up 12 semitones
chain[2] = M8ChainStep(phrase=0x00, transpose=0xF4)   # Phrase 0, down 12 semitones

project.chains[0] = chain

# Add chains to song matrix (rows x 8 tracks)
project.song[0][0] = 0x00  # Chain 0 on track 0
project.song[0][1] = 0x01  # Chain 1 on track 1
project.song[1][0] = 0x00  # Chain 0 repeats on row 1
```

### Project Metadata

```python
# Set project metadata
project.metadata.name = "MY-TRACK"
project.metadata.tempo = 140.0
project.metadata.directory = "/Songs/my-tracks/"
project.metadata.transpose = 0x00
project.metadata.key = 0x00
```

## IntEnum Classes

pym8 provides typed enum classes for FX commands and sampler parameters, making code more readable and reducing errors:

### FX Commands

- **M8SequenceFX**: Global FX commands (ARP, RET, HOP, KIL, etc.)
- **M8SamplerFX**: Sampler-specific FX commands (VOL, PIT, PLY, CUT, etc.)

### Sampler Parameters

- **M8SamplerParam**: Byte offsets for sampler parameters (VOLUME, PITCH, FILTER_TYPE, CUTOFF, etc.)
- **M8PlayMode**: Sample playback modes (FWD, REV, FWDLOOP, OSC, etc.)

These enums are defined directly in the source code (m8/api/fx.py and m8/api/sampler.py) based on the M8 file format specification.

## Examples

See the `demos/` directory for complete working examples:

- **sampler_demo.py**: Creates a project with a sampler instrument, random beats, FX commands, and chain/song arrangement
- **acid_banger_demo.py**: Algorithmic techno project with 16 rows of kick/snare/hat patterns inspired by vitling's acid-banger
  - Uses pattern generators from `acid_banger_patterns.py`
  - Random sample selection from Erica Pico sample packs
  - Random FX on hats (cut, reverse, retrigger)
  - 48 instruments across 16 rows with proper M8 song/chain/phrase structure

Run demos with:

```bash
python demos/sampler_demo.py
python demos/acid_banger_demo.py
```

Copy demos to your M8 device:

```bash
python tools/copy_demos_to_m8.py
```

## Project Structure

```
pym8/
├── m8/
│   ├── api/              # Core API modules
│   │   ├── project.py    # M8Project - top-level container
│   │   ├── instrument.py # Base instrument class
│   │   ├── sampler.py    # M8Sampler + enums
│   │   ├── phrase.py     # M8Phrase, M8PhraseStep
│   │   ├── chain.py      # M8Chain, M8ChainStep
│   │   ├── song.py       # M8SongMatrix
│   │   ├── fx.py         # M8FXTuple + FX enums
│   │   ├── metadata.py   # Project metadata
│   │   ├── modulator.py  # Modulator support
│   │   └── version.py    # Version handling
│   └── templates/        # Template .m8s files for different firmware versions
├── demos/                # Example scripts
├── tests/                # Unit tests
└── tools/                # Utility scripts
```

## File Format Reference

The M8 file format is a binary format with fixed offsets for different data sections. pym8 is based on research from these excellent open-source projects:

### Primary Reference

- **[m8-file-parser](https://github.com/Twinside/m8-file-parser)** (Rust)

  The most complete and authoritative M8 file format parser. This project documents:
  - Binary structure layouts
  - FX command codes and their values
  - Instrument parameter offsets
  - Version-specific format changes (firmware 4.0 - 6.2+)

  **All FX enums and sampler parameter offsets in pym8 are based on this project.**

### Additional References

- **[m8-js](https://github.com/whitlockjc/m8-js)** - JavaScript implementation with good format documentation
- **[m8-files](https://github.com/AlexCharlton/m8-files)** - Original Rust parser that inspired m8-file-parser

### Official Resources

- **[Dirtywave M8 Tracker](https://dirtywave.com/products/m8-tracker)** - Official M8 hardware
- **[M8 Headless](https://github.com/Dirtywave/M8Headless)** - Official headless M8 firmware

## Firmware Compatibility

pym8 targets M8 firmware version **6.2+** by default. Template files are included for different firmware versions:

- `TEMPLATE-4-0-2.m8s` - Firmware 4.0.2
- `TEMPLATE-5-0-1.m8s` - Firmware 5.0.1
- `TEMPLATE-6-2-1.m8s` - Firmware 6.2.1 (current)

Key differences across versions:
- **V2**: Initial format (23 sequence commands)
- **V3**: Added RND, RNL, RMX, PBN, TBX, OFF commands
- **V4**: Expanded instrument commands
- **V6.2**: Latest format with additional mixer commands (XRH, XMT, OTT, OTC, OTI)

## Data Types and Conventions

All M8 data uses:
- **Little-endian byte order** for multi-byte values
- **Unsigned 8-bit integers** (0x00-0xFF) for most parameters
- **Null-terminated strings** for text fields
- **Float32** for tempo (4 bytes, little-endian)

## Development

### Running Tests

```bash
python run_tests.py
```

### Project Configuration

The project uses `pyproject.toml` for configuration (PEP 518) with setuptools as the build backend.

## License

MIT License

## Credits

Created by jhw (justin.worrall@gmail.com)

Special thanks to:
- [Twinside](https://github.com/Twinside) for the comprehensive [m8-file-parser](https://github.com/Twinside/m8-file-parser) Rust library
- [whitlockjc](https://github.com/whitlockjc) for [m8-js](https://github.com/whitlockjc/m8-js)
- [AlexCharlton](https://github.com/AlexCharlton) for [m8-files](https://github.com/AlexCharlton/m8-files)
- [Dirtywave](https://dirtywave.com/) for creating the M8 Tracker

## Contributing

Contributions are welcome! When adding new features:

1. Verify against [m8-file-parser](https://github.com/Twinside/m8-file-parser) for accuracy
2. Include practical examples in code
3. Add tests for new functionality
4. Document any firmware version-specific features

## Support

- **Issues**: [GitHub Issues](https://github.com/jhw/pym8/issues)
- **Examples**: See `demos/` directory
- **Tests**: Check `tests/` directory for API usage examples
