# pym8

A Python library for reading and writing DirtyWave M8 tracker files.

## Overview

pym8 is a Python package for programmatically creating, reading, and manipulating M8 project files (.m8s). The M8 is a portable music tracker and synthesizer by [Dirtywave](https://dirtywave.com/products/m8-tracker).

This library provides a high-level API for working with M8 projects, including:
- Creating and modifying instruments (sampler, wavsynth, macrosynth, FM, external MIDI)
- Building phrases with notes and FX commands
- Arranging chains and song sequences
- Reading and writing .m8s project files
- Audio utilities for sample chains and WAV slicing

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
from m8.api.instruments.sampler import M8Sampler, M8SamplerParam
from m8.api.phrase import M8Phrase, M8PhraseStep, M8Note
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
        note=M8Note.C_4,  # C4
        velocity=0x6F,    # Full velocity
        instrument=0x00   # Use instrument slot 0
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

pym8 supports all M8 instrument types with full parameter control:

- **M8Sampler** - Sample playback with slicing, looping, and pitch modes
- **M8Wavsynth** - Wavetable synthesizer with 16 waveforms
- **M8Macrosynth** - Mutable Instruments Braids-based synthesis (45 algorithms)
- **M8FMSynth** - 4-operator FM synthesizer
- **M8External** - MIDI output to external hardware/software

#### Sampler Example

```python
from m8.api.instruments.sampler import M8Sampler, M8SamplerParam, M8PlayMode

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

#### Wavsynth Example

```python
from m8.api.instruments.wavsynth import M8Wavsynth, M8WavsynthParam, M8WavsynthShape

wavsynth = M8Wavsynth(name="LEAD")
wavsynth.set(M8WavsynthParam.SHAPE, M8WavsynthShape.SAW)
wavsynth.set(M8WavsynthParam.SIZE, 0x80)
wavsynth.set(M8WavsynthParam.MULT, 0x01)
wavsynth.set(M8WavsynthParam.CUTOFF, 0xA0)
```

#### Macrosynth Example

```python
from m8.api.instruments.macrosynth import M8Macrosynth, M8MacrosynthParam, M8MacrosynthShape

macro = M8Macrosynth(name="BASS")
macro.set(M8MacrosynthParam.SHAPE, M8MacrosynthShape.CSAW)
macro.set(M8MacrosynthParam.TIMBRE, 0x60)
macro.set(M8MacrosynthParam.COLOR, 0x40)
```

#### FMSynth Example

```python
from m8.api.instruments.fmsynth import M8FMSynth, M8FMSynthParam

fm = M8FMSynth(name="BELL")
fm.set(M8FMSynthParam.ALGO, 0x00)
fm.set(M8FMSynthParam.RATIO_A, 0x01)
fm.set(M8FMSynthParam.RATIO_B, 0x02)
```

#### External (MIDI Out) Example

```python
from m8.api.instruments.external import M8External, M8ExternalParam, M8ExternalPort

ext = M8External(name="SYNTH")
ext.set(M8ExternalParam.PORT, M8ExternalPort.MIDI)
ext.set(M8ExternalParam.CHANNEL, 0x00)  # Channel 1
ext.set(M8ExternalParam.BANK, 0x00)
ext.set(M8ExternalParam.PROGRAM, 0x00)
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

### Audio Tools

pym8 includes utilities for working with audio samples:

#### ChainBuilder - Create Sliced Sample Chains

Combine multiple samples into a single sliced WAV file for M8's sample slicing feature:

```python
from m8.tools.chain_builder import ChainBuilder

# Build a chain from multiple samples
builder = ChainBuilder(
    sample_duration_ms=500,     # Duration per slice
    fade_ms=5,                  # Fade in/out to prevent clicks
    target_frame_rate=44100     # Output sample rate
)

samples = ["kick.wav", "snare.wav", "hat.wav", "clap.wav"]
wav_data, slice_mapping = builder.build_chain(samples)

# wav_data: BytesIO containing the combined WAV with slice metadata
# slice_mapping: dict mapping original sample index to slice index
```

#### WAVSlicer - Add Slice Points to WAV Files

Add M8-compatible slice metadata to existing WAV files:

```python
from m8.tools.wav_slicer import WAVSlicer

# Add slice points to a WAV file
slicer = WAVSlicer()
slice_points = [0, 22050, 44100, 66150]  # Sample positions
sliced_wav = slicer.add_slice_points(wav_data, slice_points)
```

## IntEnum Classes

pym8 provides typed enum classes for FX commands and sampler parameters, making code more readable and reducing errors:

### FX Commands

- **M8SequenceFX**: Global FX commands (ARP, RET, HOP, KIL, etc.)
- **M8SamplerFX**: Sampler-specific FX commands (VOL, PIT, PLY, CUT, etc.)

### Sampler Parameters

- **M8SamplerParam**: Byte offsets for sampler parameters (VOLUME, PITCH, FILTER_TYPE, CUTOFF, etc.)
- **M8PlayMode**: Sample playback modes (FWD, REV, FWDLOOP, OSC, etc.)

### Notes

- **M8Note**: Note values from C1 (0) to G11 (127)
  - Dynamically generated with format: `C_1`, `CS_1`, `D_1`, ..., `C_4` (36/0x24), ..., `G_11`
  - M8 octave numbering: byte 0 = C1, so C4 = 36 (0x24)

These enums are defined in the source code (m8/api/fx.py, m8/api/instruments/sampler.py, and m8/api/phrase.py) based on the M8 file format specification.

## Examples

The `demos/` directory contains complete working examples organized by category:

### Acid 303 Basslines (`demos/acid_303/`)

Classic 303-style acid bassline generators with multiple synthesis options:

- **sampler.py** - Sampler-based acid with sample playback
- **wavsynth.py** - Wavetable synthesis acid basslines
- **macrosynth.py** - Braids-based synthesis for acid sounds
- **midi.py** - MIDI output to external 303/synth hardware

### Acid 909 Drums (`demos/acid_909/`)

Algorithmic 909 drum patterns inspired by vitling's acid-banger:

- **sampler.py** - Sample-based drum machine
- **synthdrums.py** - Synthesized drums using Macrosynth
- **chain.py** - Chain arrangement demonstration
- **midi.py** - MIDI output to external drum machines

### Euclidean Rhythms (`demos/euclid/`)

Euclidean rhythm patterns using the Bjorklund algorithm:

- **sampler.py** - Sample-based Euclidean rhythms
- **midi.py** - MIDI output for Euclidean patterns

Based on [Bjorklund algorithm](https://github.com/brianhouse/bjorklund) and [Toussaint's research](https://cgm.cs.mcgill.ca/~godfried/publications/banff.pdf). Generates traditional world music rhythms (Cuban tresillo, African bell patterns, Brazilian rhythms) with groove algorithms inspired by Erica Synths Perkons HD-01.

### Chord Progressions (`demos/chords/`)

Harmonic examples and chord generators:

- **synth.py** - Synthesizer-based chord progressions
- **midi.py** - MIDI chord output

### Reusable Pattern Libraries (`demos/patterns/`)

Pattern generators that can be imported into your own projects:

- **acid_303.py** - 303 bassline pattern generators
- **acid_909.py** - 909-style drum patterns (kick, snare, hat, clap variations)
- **euclidean.py** - Bjorklund algorithm implementation for Euclidean rhythms

### Utilities (`demos/utils/`)

- **download_erica_pico_samples.py** - Downloads Erica Synths Pico Drum sample packs

### Running Demos

```bash
# Download samples first (required for sample-based demos)
python demos/utils/download_erica_pico_samples.py

# Run demos (examples)
python demos/acid_303/sampler.py
python demos/acid_909/sampler.py
python demos/euclid/sampler.py
python demos/chords/synth.py
```

### Managing Demos on M8

```bash
# Copy demos to M8 device
python tools/copy_demos_to_m8.py

# Copy specific demos (filter by pattern)
python tools/copy_demos_to_m8.py acid-303

# Test mode (dry run)
python tools/copy_demos_to_m8.py --test

# Clean demos from M8
python tools/clean_demos_from_m8.py

# Clean local demo output files
python tools/clean_local_demos.py
```

## Project Structure

```
pym8/
├── m8/
│   ├── api/                    # Core API modules
│   │   ├── project.py          # M8Project - top-level container
│   │   ├── instrument.py       # Base M8Instrument class + M8Instruments collection
│   │   ├── phrase.py           # M8Phrase, M8PhraseStep, M8Note
│   │   ├── chain.py            # M8Chain, M8ChainStep
│   │   ├── song.py             # M8SongMatrix (255 rows × 8 tracks)
│   │   ├── fx.py               # M8FXTuple + M8SequenceFX, M8SamplerFX enums
│   │   ├── metadata.py         # Project metadata (name, tempo, key)
│   │   ├── modulator.py        # M8Modulators (AHD, ADSR, LFO, etc.)
│   │   ├── midi_settings.py    # MIDI configuration
│   │   ├── version.py          # Firmware version handling
│   │   └── instruments/        # Instrument type implementations
│   │       ├── sampler.py      # M8Sampler - sample playback
│   │       ├── wavsynth.py     # M8Wavsynth - wavetable synthesis
│   │       ├── macrosynth.py   # M8Macrosynth - Braids-based synthesis
│   │       ├── fmsynth.py      # M8FMSynth - 4-operator FM synthesis
│   │       └── external.py     # M8External - MIDI output to hardware
│   ├── tools/                  # Audio utilities
│   │   ├── chain_builder.py    # Build sample chains with slice metadata
│   │   └── wav_slicer.py       # Add slice points to WAV files
│   └── templates/              # Template .m8s files for different firmware versions
├── demos/                      # Example scripts organized by category
│   ├── acid_303/               # 303-style acid basslines
│   ├── acid_909/               # 909 drum machine patterns
│   ├── euclid/                 # Euclidean rhythm patterns
│   ├── chords/                 # Chord progression examples
│   ├── patterns/               # Reusable pattern generators
│   ├── lib/                    # Helper libraries
│   └── utils/                  # Utility scripts (sample downloads, etc.)
├── tests/                      # Unit tests
└── tools/                      # Project management scripts
    ├── copy_demos_to_m8.py     # Copy demos to M8 device
    ├── clean_demos_from_m8.py  # Remove demos from M8 device
    └── clean_local_demos.py    # Clean up local demo files
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

- **[m8-js](https://github.com/whitlockjc/m8-js)** - JavaScript implementation with comprehensive enum documentation

  This project is particularly valuable for enum information (FX commands, parameter values, play modes, etc.). However, it targets M8 firmware version 4.0 and is no longer actively maintained. Since the M8 is now at firmware 6.2+, **do not use m8-js for offset information** as binary structure layouts change between versions. The enum data (command codes, parameter ranges, mode values) remains reliable and stable.

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
