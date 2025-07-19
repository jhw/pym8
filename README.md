# PyM8

A Python library for reading and writing Dirtywave M8 tracker files.

## Overview

PyM8 provides a complete Python interface for working with M8 tracker binary files (.m8s project files and .m8i instrument files). The library handles the complete M8 file format including:

- **Project Files (.m8s)**: Complete M8 songs with all data
- **Instrument Files (.m8i)**: Individual M8 instruments
- **Metadata**: Song information, BPM, key, scale
- **Song Structure**: Pattern arrangement and sequencing
- **Phrases**: Note sequences with timing and effects
- **Chains**: Phrase sequences with transposition
- **Instruments**: All 5 M8 synthesizer types with full parameter support
- **Effects**: Sequencer, mixer, and modulator effects
- **Modulators**: Envelopes and LFOs for parameter automation

## Features

- **Read & Write**: Full bidirectional support for M8 files
- **Format Validation**: Built-in validation for M8 file structure
- **Type Safety**: Comprehensive enums for all M8 parameters
- **Extensible**: Modular design for easy customization
- **Version Support**: Handles multiple M8 firmware versions
- **Test Coverage**: Comprehensive test suite with 292 tests

## Installation

```bash
pip install pym8
```

## Quick Start

### Loading an M8 Project

```python
from m8.api.project import M8Project

# Load a complete M8 project file
project = M8Project.read_from_file("song.m8s")

# Access project components
print(f"Song: {project.metadata.name}")
print(f"BPM: {project.metadata.tempo_bpm}")
print(f"Key: {project.metadata.key}")

# Work with instruments
instruments = project.instruments
for i, instr in enumerate(instruments):
    if not instr.is_empty():
        print(f"Instrument {i}: {instr.name} ({instr.instrument_type})")
```

### Working with Instruments

```python
from m8.api.instruments import M8Sampler, M8FMSynth
from m8.enums import M8InstrumentType

# Create a new sampler instrument
sampler = M8Sampler(
    name="My Sample",
    volume=128,
    pitch=64
)

# Set sampler-specific parameters
sampler.params.slice_start = 0
sampler.params.slice_length = 255
sampler.params.loop_start = 0

# Create an FM synth
fm_synth = M8FMSynth(
    name="Bass Synth",
    volume=200
)

# Set FM parameters
fm_synth.params.algo = 1
fm_synth.params.mod_1 = 64
fm_synth.params.mod_2 = 32

# Save instrument to file
fm_synth.write_to_file("bass.m8i")
```

### Working with Effects and Modulators

```python
from m8.api.modulators import M8LFO, M8ADSREnvelope
from m8.enums import M8SequencerFX

# Create an LFO modulator
lfo = M8LFO(
    destination=0x10,  # Target parameter
    amount=64,
    freq=32,
    shape=1
)

# Add modulator to instrument
sampler.add_modulator(lfo)

# Create ADSR envelope
adsr = M8ADSREnvelope(
    destination=0x08,  # Volume
    attack=16,
    decay=32,
    sustain=128,
    release=64
)

sampler.add_modulator(adsr)
```

### Creating Projects

```python
from m8.api.project import M8Project
from m8.api.metadata import M8Metadata

# Create new project
project = M8Project()

# Set metadata
project.metadata = M8Metadata(
    name="My Song",
    tempo_bpm=140,
    key=0,  # C
    scale=0  # Chromatic
)

# Add instruments
project.instruments[0] = sampler
project.instruments[1] = fm_synth

# Save project
project.write_to_file("new_song.m8s")
```

## Project Structure

```
m8/
├── api/                    # Main API classes
│   ├── chains.py          # Chain and step management
│   ├── fx.py              # Effects processing
│   ├── instruments/       # Instrument implementations
│   │   ├── fmsynth.py    # FM synthesizer
│   │   ├── hypersynth.py # Hypersynth
│   │   ├── macrosynth.py # Macrosynth
│   │   ├── sampler.py    # Sample playback
│   │   └── wavsynth.py   # Wavetable synth
│   ├── metadata.py        # Song metadata
│   ├── modulators.py      # Envelope and LFO modulators
│   ├── phrases.py         # Note sequences
│   ├── project.py         # Complete M8 projects
│   ├── song.py            # Song arrangement
│   └── version.py         # M8 firmware version
├── core/                  # Core utilities
│   ├── utils/            # Utility functions
│   └── validation.py     # Format validation
├── enums/                 # Type definitions
│   ├── fmsynth.py        # FM synth enums
│   ├── hypersynth.py     # Hypersynth enums
│   ├── macrosynth.py     # Macrosynth enums
│   ├── sampler.py        # Sampler enums
│   └── wavsynth.py       # Wavsynth enums
├── tools/                 # Additional tools
│   ├── chain_builder.py   # Chain construction utilities
│   ├── slice_extractor.py # Audio slicing tools
│   └── wav_slicer.py      # WAV file processing
├── config.py              # Configuration management
└── format_config.yaml     # M8 format specification
```

## Instrument Types

PyM8 supports all M8 synthesizer types:

- **WAVSYNTH** (0x00): Wavetable synthesizer
- **MACROSYNTH** (0x01): Macro-controlled synthesizer  
- **SAMPLER** (0x02): Sample playback engine
- **FMSYNTH** (0x04): 4-operator FM synthesis
- **HYPERSYNTH** (0x05): Advanced synthesizer

Each instrument type has its own parameter set and capabilities defined in the respective modules.

## Effects System

M8 effects are organized into three categories:

- **Sequencer Effects**: Pattern-based effects (ARP, DEL, GRV, etc.)
- **Mixer Effects**: Audio processing effects (reverb, delay, EQ, etc.)
- **Modulator Effects**: Parameter automation (envelopes, LFOs)

## Testing

Run the comprehensive test suite:

```bash
python run_tests.py
```

The test suite includes:
- Binary format validation
- Round-trip serialization tests
- Instrument parameter validation
- Effect and modulator tests
- Project file integrity tests

## Development Tools

The `dev_tools/` directory contains utilities for:
- Inspecting M8 file contents
- Extracting individual instruments
- Analyzing binary data structure
- Version compatibility checking

## License

MIT License - see LICENSE file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass: `python run_tests.py`
5. Submit a pull request

## References

- [Dirtywave M8 Tracker](https://dirtywave.com/products/m8-tracker)
- [M8 File Format Documentation](https://github.com/AlexCharlton/m8-files)