# M8 Library Architecture

## Overview

The M8 library is a Python package for reading, writing, and manipulating Dirtywave M8 tracker files (`.m8s`, `.m8i`). It provides a clean, object-oriented API over the low-level binary format used by the hardware device.

## Core Architecture

### Component Hierarchy

The library uses a hierarchical structure that mirrors the M8 hardware:

1. **Project** (`M8Project`): The top-level container representing an entire song file
   - Contains multiple instruments, phrases, chains, and the song matrix
   - Handles file I/O operations for reading/writing M8S files
   - Manages metadata and version information

2. **Instruments** (`M8Instrument` subclasses): Sound generators
   - Multiple types: WavSynth, MacroSynth, Sampler, FMSynth, HyperSynth
   - Each has type-specific parameters and behaviors
   - Can be saved/loaded as standalone M8I files

3. **Modulators** (`M8Modulator`): Parameter modulation sources
   - Different types: AHD Envelope, LFO, etc.
   - Connected to instruments to modulate parameters
   - Can target different destinations depending on instrument type

4. **Phrases** (`M8Phrase`): Sequences of notes and effects
   - Contains steps with note, velocity, and instrument information
   - Includes FX commands for each step

5. **Chains** (`M8Chain`): Sequences of phrases 
   - References phrases by index
   - Controls phrase transposition and playback

6. **Song** (`M8Song`): Arrangement of chains
   - Contains the complete song structure
   - Maps chains to tracks and positions

### Base Classes

The library uses several core base classes to handle binary data:

- **M8Block**: Fundamental building block for raw binary data
- **M8ValidationResult**: Error tracking and validation reporting
- **EnumPropertyMixin**: Provides enum conversion for properties

## Binary Format Handling

### Design Approach

The library takes a structured approach to binary data handling:

1. **Configuration-Driven**: Binary format definitions are stored in YAML
   - Field offsets, types, and defaults defined in configuration
   - Supports different file format versions

2. **Read/Write Pattern**: Classes implement a consistent interface
   - `read(data)`: Class method to deserialize binary data
   - `write()`: Instance method to serialize to binary data
   - `read_from_file(filename)`: Convenient file I/O
   - `write_to_file(filename)`: Convenient file I/O

3. **Field Types**: Supports various field types
   - Basic: UINT8, INT8, UINT16, etc.
   - Composite: UINT4_2 (two 4-bit values in a byte)
   - Arrays: Fixed-size arrays of values
   - Strings: Fixed-length strings with termination handling

### Serialization/Deserialization

Beyond binary format, the library provides JSON serialization:

- **as_dict()**: Convert to dictionary representation
- **from_dict()**: Create from dictionary representation
- **JSON encoders/decoders**: Custom handling for M8-specific types

## Enum Support System

The library uses enums extensively to make the API more intuitive:

### Context-Aware Enums

- **M8InstrumentContext**: Singleton context manager
  - Tracks current instrument type for enum resolution
  - Allows proper serialization of instrument-specific enums
  - Used by FX and modulator parameters

### Enum Conversion

- **String ⟷ Numeric**: Bidirectional conversion between:
  - Human-readable enum names ("SINE", "REVERB")
  - Numeric values used in binary format (0x01, 0x02)

### Decorator-Based Parameter Conversion

- **with_enum_param**: Decorator for methods accepting enum strings
  - Automatically converts string parameters to numeric values
  - Maintains API simplicity while handling complexity internally

## Validation System

The library includes a comprehensive validation system:

### M8ValidationResult

- **Hierarchical validation**: Tracks component relationships
- **Error collection**: Aggregates errors with context paths
- **Flexible reporting**: Can raise exceptions or return results

### Validation Types

- **Reference validation**: Ensures relationships between components are valid
- **Completeness validation**: Checks required fields are present
- **Version validation**: Ensures consistent versions across components

## Design Patterns

Several design patterns are used throughout the codebase:

### Creational Patterns

- **Factory Methods**: Create appropriate instance types
- **Builder methods**: Construct objects from dictionaries or lists

### Structural Patterns

- **Decorator**: Add behavior to methods (enum conversion)
- **Composite**: Hierarchical structure of components
- **Adapter**: Convert between different representations

### Behavioral Patterns

- **Strategy**: Different instrument types with specialized behavior
- **Command**: Operations encapsulated in objects
- **Observer**: Context manager observes instrument references

## Practical Design Decisions

### No Type Annotations

- The library deliberately avoids Python type hints
- Clear naming conventions and documentation provide type clarity

### Minimal Dependencies

- Core functionality has no external dependencies beyond standard library
- Optional features clearly separate required vs. optional dependencies

### Error Handling

- Custom exceptions for different error types
- Validation system provides contextual error information
- Proper fallback mechanisms for backward compatibility

## Extensions and Tooling

### Developer Tools

- Inspection tools for examining M8 files
- Extraction utilities for working with samples
- Visualization helpers for understanding file structure

### Client Utilities

- WAV slicer for creating sliced samples
- Phrase concatenation for building longer sequences
- Chain baking for flattening arrangements