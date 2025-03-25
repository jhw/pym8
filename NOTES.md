# Proposed Instrument Context Manager

## Overview (25/03/25)

The current implementation couples instruments directly with their children (modulators, FX) by passing the `instrument_type` explicitly. This creates tight coupling and makes it challenging to handle cases where context needs to be determined dynamically (like FX in phrases).

A context manager approach would provide a more flexible, decoupled solution:

```python
class M8InstrumentContext:
    """Context manager for instrument-related operations."""
    
    _instance = None  # Singleton instance
    
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
        
    def __init__(self):
        self.project = None
        self.current_instrument_id = None
        self.current_instrument = None
        
    def set_project(self, project):
        """Set the current project context."""
        self.project = project
        
    def get_instrument_type(self, instrument_id=None):
        """Get instrument type for a given instrument ID or current instrument."""
        if instrument_id is not None:
            # Look up instrument type by ID
            if self.project and 0 <= instrument_id < len(self.project.instruments):
                instrument = self.project.instruments[instrument_id]
                return getattr(instrument, 'instrument_type', None)
        elif self.current_instrument_id is not None:
            # Use current instrument from context
            if self.project and 0 <= self.current_instrument_id < len(self.project.instruments):
                instrument = self.project.instruments[self.current_instrument_id]
                return getattr(instrument, 'instrument_type', None)
        return None
        
    def with_instrument(self, instrument_id):
        """Context manager for operations with a specific instrument."""
        return _InstrumentContextBlock(self, instrument_id)

class _InstrumentContextBlock:
    """Context block for instrument operations."""
    def __init__(self, manager, instrument_id):
        self.manager = manager
        self.instrument_id = instrument_id
        self.previous_id = None
        
    def __enter__(self):
        self.previous_id = self.manager.current_instrument_id
        self.manager.current_instrument_id = self.instrument_id
        return self.manager
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.manager.current_instrument_id = self.previous_id
```

## Usage Examples

### 1. For Modulators (replacing direct coupling)

Current approach:
```python
modulator = M8Modulator(modulator_type=type, instrument_type=instrument.instrument_type)
modulator_dict = modulator.as_dict()  # Needs instrument_type for proper enum serialization
```

With context manager:
```python
context = M8InstrumentContext.get_instance()
with context.with_instrument(instrument_idx):
    modulator = M8Modulator(modulator_type=type)  # No instrument_type needed
    modulator_dict = modulator.as_dict()  # Uses context for enum serialization
```

### 2. For FX in Phrase Steps

Current issue: FX in phrase steps need the instrument type for proper enum serialization, but there's no clean way to propagate this information.

With context manager:
```python
# When serializing a phrase step
def step_as_dict(self):
    result = {...}
    
    # If this step references an instrument, set context for FX serialization
    if self.instrument != 0xFF:  # Not empty
        context = M8InstrumentContext.get_instance()
        with context.with_instrument(self.instrument):
            # FX serialization will automatically use the instrument context
            result["fx"] = self.fx.as_list()
    else:
        # No instrument context needed
        result["fx"] = self.fx.as_list()
    
    return result
```

## Benefits

1. **Decoupled Design**: Objects no longer need direct references to their parent context
2. **Flexible Context Resolution**: Can resolve instrument type from either explicit ID or current context
3. **Consistent API**: Same mechanism works for all places needing instrument context (modulators, FX, etc.)
4. **Improved Testability**: Easy to set up test contexts without creating full object hierarchies
5. **Simplified Parameter Passing**: No more passing instrument_type through multiple layers

## Implementation Strategy

1. Create the context manager in m8/api/utils/context.py
2. Modify FX and modulator serialization to use the context manager
3. Update the phrase step serialization to establish instrument context for FX
4. Maintain backward compatibility with the existing explicit instrument_type parameters
5. Gradually transition away from explicit coupling in future versions

# Enum Implementation Improvement Opportunities

## Enum Implementation Design Decision (28/03/25)

The codebase uses two complementary patterns for enum handling that align with the different requirements of their respective class types:

### 1. Fixed-property pattern
Classes with properties known at design time (M8FXTuple, M8PhraseStep, M8Instrument) use:
- Direct property access with explicit property names
- EnumPropertyMixin for enum conversion utilities
- Properties with well-defined behavior and explicit getters/setters
- Straightforward serialization/deserialization for known fields

### 2. Dynamic-property pattern
Classes where properties vary based on configuration (M8InstrumentParams, M8ModulatorParams) use:
- Generic attribute access (setattr/getattr) based on configuration
- Parameter definitions loaded from configuration
- Dictionary-based property storage
- Flexible serialization/deserialization that adapts to different types

### Design Rationale

We considered implementing a descriptor-based pattern to reduce boilerplate code, but decided against it for several reasons:

1. **Conceptual clarity**: Having two fundamentally different patterns would create a deeper division in the codebase
2. **Applicability limitations**: The descriptor pattern works well for fixed properties but not for dynamic ones
3. **Learning curve**: Making part of the codebase use a different pattern would increase cognitive load
4. **Maintainability**: Having a mix of patterns could lead to inconsistent behavior as the codebase evolves

Instead, we chose to maintain the existing approach, which already uses shared utility functions from `m8/api/utils/enums.py` that provide consistent enum conversion across both patterns.

### Future Improvements

To reduce code duplication while maintaining the consistent approach:

1. **Centralized enum conversion**: Create more utility functions for common patterns
2. **Unified serialization approaches**: Standardize how as_dict/from_dict methods handle enums
3. **Explicit validation**: Add methods to verify enum values against their allowed sets
4. **Better documentation**: Clearly document the intended patterns for both class types

## Potential Enum Abstraction Improvements

While the current implementation already handles context-aware enum resolution through the dictionary-based configuration and proper context propagation, there are still opportunities to reduce code duplication and improve maintainability:

1. **Centralized enum conversion**: The common pattern of checking if a value is empty, then checking if it has enum mappings, and finally converting it could be centralized into a single utility function while maintaining the current pattern.

2. **Unified serialization API**: The variability between client classes' serialization logic could be standardized into a protocol or abstract base class that implements common patterns.

3. **Explicit enum validation**: Currently, validation is separate from the is_empty() checks. A more comprehensive API could include explicit validation methods that verify enum values against their allowed sets.

4. **Reduce boilerplate**: Consider refactoring to reduce repetitive code while maintaining a single, consistent pattern across all classes in the codebase.

The most important consideration is maintaining a unified, consistent approach to enum handling throughout the codebase. Any improvements should be applicable to both classes with fixed property sets and those with dynamic, configuration-driven properties.

## Modulator Destination Enum Serialization Issue

### Read Method Issue (25/03/25)

We've discovered an issue with modulator destination enum serialization related to the parent-child relationship between instruments and modulators:

1. When instruments and their modulators are read from binary data, the parent-child relationship isn't properly established
2. Specifically, the `instrument_type` isn't set on modulators during the read process
3. This means that modulators don't have the context they need to properly convert numeric enum values to string names
4. For example, a destination value of 1 should be converted to "VOLUME", but without knowing the parent instrument type, this can't happen automatically

### Steps Needed:

1. Modify the instrument read method to set the `instrument_type` on each modulator after reading it
2. This would involve updating `M8Instrument.read()` to set the instrument_type on each modulator after reading the modulators
3. Ensure the instrument type is set before calling as_dict() on modulators
4. Update tests to verify that enum values are properly serialized after reading from binary

### Implementation Note (25/03/25)

The implementation for context-aware modulator enums can leverage the existing infrastructure:

1. The codebase already has instrument-specific enums and utilities that support context-aware enum handling
2. The configuration in format_config.yaml already maps instrument types to their relevant enum mappings
3. The fix is straightforward - update M8Instrument.read() to establish the parent-child relationship during deserialization
4. Once the parent context is available, the existing enum utilities will handle conversion between string names and numeric values automatically
5. This approach completes the consistent external enum usage across the entire API, making modulator destinations use string enum values just like all other enum fields

### Context Manager Issues (28/03/25)

After implementing the instrument context manager system, we discovered issues with enum serialization:

1. The context manager singleton approach works correctly for operations that occur within a context block, but context isn't always maintained between operations:
   - When an instrument creates a modulator, the context is correctly set
   - However, when the modulator is later serialized (as_dict) outside the original context, it loses its parent context

2. Even with context handling in serialize_param_enum_value, if the modulator destination is an integer value, the serialization won't work correctly unless:
   - The modulator has its instrument_type explicitly set (tight coupling), or
   - The modulator is being serialized within an instrument context block

3. Solutions to consider:
   - Ensure `serialize_param_enum_value`, `deserialize_param_enum`, and `ensure_enum_int_value` all check context when instrument_type is None
   - Update all enum utility functions to properly fall back to the context manager
   - Make sure M8Modulators.as_list() passes context to each modulator
   - Add context-aware overrides to tools that need enum string representations

## YAML Serialization Issue (26/03/25)

When examining the output of tools/inspect_instruments.py, we noticed that 'OFF' enum values appear with single quotes in YAML output (e.g., `destination: 'OFF'`), while other enum values don't have quotes (e.g., `destination: VOLUME`). This occurs because:

1. 'OFF' is a reserved word in YAML that normally means 'false' (like 'off', 'no', or 'false')
2. The YAML serializer automatically quotes such reserved words to prevent them from being interpreted as boolean values

Potential solutions:
1. Modify the YAML repr in tools/inspect_instruments.py to avoid quoting these values
2. More fundamentally, modify the enum serialization functions in m8/api/utils/enums.py to:
   - Detect YAML keywords in enum values
   - Return a modified string (e.g., '_OFF' instead of 'OFF') that won't be recognized as a YAML keyword
   - This would require changes to both serialization and deserialization to maintain consistency

Given the limited impact (only affects display in the inspect_instruments tool), this can be addressed in a future update.

# Notes on standardizing enum string case

## Changes Made (24/03/25)

1. Updated YAML configuration in `m8/format_config.yaml`:
   - Changed instrument types from lowercase ("wavsynth", "macrosynth", "sampler") to uppercase ("WAVSYNTH", "MACROSYNTH", "SAMPLER")
   - Changed modulator types from lowercase ("ahd_envelope", "lfo", etc.) to uppercase ("AHD_ENVELOPE", "LFO", etc.)

2. Updated configuration handling in `m8/config.py`:
   - Modified `get_instrument_types()` to return uppercase type names
   - Modified `get_modulator_types()` to return uppercase type names
   - Added case-insensitive lookup for type IDs and data with fallback to both uppercase and lowercase
   - All accessors now handle both uppercase and lowercase for backward compatibility

3. Fixed the instrument constructor code to work with the updated config format

4. Updated instrument and modulator handling:
   - Modified `M8InstrumentParams.from_config()` to handle uppercase consistently
   - Modified `M8ModulatorParams.from_config()` to handle uppercase consistently
   - Added a simple `is_empty()` implementation to instruments and collections
   - Temporarily commented out test_is_empty tests that had inconsistent expectations
   
5. Used a script-based approach to efficiently update all enum string references:
   - Created a script to recursively find and replace all lowercase references
   - Target strings included instrument_type, modulator_type, and enum assertions
   - All tests now refer to uppercase enum strings consistently

## Future Work

1. There are still some test failures related to expected string case in tests
   - Some tests expect "lfo" but now get "LFO"
   - Some tests expect "sampler" but now get "SAMPLER"
   - These could be fixed by either:
     - Updating all tests to expect uppercase
     - Making the code normalize the case to what the tests expect

2. Consider exposing a utility function to normalize enum case for consistency

## Backward Compatibility

The config loading functions now handle both uppercase and lowercase variants of instrument
and modulator types, so code that uses the lowercase versions should continue to work.

# Default Field Properties in Configuration

## Default rules:

1. If a field has no explicit `size`, `type`, or `default`, the following are applied:
   - `size: 1`
   - `type: "UINT8"`
   - `default: 0`

2. This applies to most instrument parameters, modulator fields, and other common fields.

3. These defaults should be used to simplify the configuration YAML file.

## Example:

Current verbose format:
```yaml
transpose: {offset: 128, size: 1, type: "UINT8", default: 0}
```

Simplified format:
```yaml
transpose: {offset: 128}
```

## Implementation notes:

When loading field definitions from YAML:
1. Check if `size` is missing and add default `size: 1`
2. Check if `type` is missing and add default `type: "UINT8"`
3. Check if `default` is missing and add default `default: 0`
4. Apply these defaults at configuration load time

# UINT4_2 Field Type

## Overview

The UINT4_2 field type represents a byte that contains two 4-bit values packed together. This is common in the M8 format where multiple parameters are stored efficiently in a single byte.

## Format in Configuration

A UINT4_2 field is defined with a special structure that describes both its overall properties and its component parts:

```yaml
transpose_eq:
  offset: 13
  type: "UINT4_2"
  components:
    transpose:
      nibble: 1  # Lower nibble (bits 0-3)
      default: 4
    eq:
      nibble: 2  # Upper nibble (bits 4-7)
      default: 1
```

## Key Components

1. The main field defines:
   - `offset`: Byte position in the data structure
   - `type`: Set to "UINT4_2" to indicate this is a composite field

2. The `components` section lists the individual nibble values:
   - Each component has its own name (e.g., "transpose", "eq")
   - `nibble`: Indicates which nibble (1 for lower, 2 for upper)
   - `default`: Default value for this component

## Processing

When reading/writing this field:
1. The byte at the specified offset contains both values
2. The lower 4 bits (nibble 1) contain the first value
3. The upper 4 bits (nibble 2) contain the second value
4. These are split/joined using `split_byte()` and `join_nibbles()` utilities

## Benefits

This structure provides several advantages:
1. Self-documenting configuration that clearly shows which parameters are combined
2. Consistent field model for all types of fields
3. Makes the relationships between parameters explicit
4. Maintains backward compatibility with existing code that uses the combined field

### fmsynth mods 22/03/25

 Now I see the issue more clearly. The MOD_OFFSET is a critical value that determines where modulators are written
  relative to SynthParams content. Let me recalculate the absolute byte positions by carefully tracing the code flow:

  WavSynth:
  - Common fields: 12 + 1 + 1 + 3 = 17 bytes
  - Synth-specific fields: 5 bytes (shape, size, mult, warp, scan)
  - SynthParams begins at byte 22
  - SynthParams.write() is called with MOD_OFFSET = 30
  - This means modulators are written starting at position 22 + 30 = 52 bytes from the start

  MacroSynth:
  - Common fields: 12 + 1 + 1 + 3 = 17 bytes
  - Synth-specific fields: 5 bytes (shape, timbre, color, degrade, redux)
  - SynthParams begins at byte 22
  - SynthParams.write() is called with MOD_OFFSET = 30
  - This means modulators are written starting at position 22 + 30 = 52 bytes from the start

  FMSynth:
  - Common fields: 12 + 1 + 1 + 3 = 17 bytes
  - algo: 1 byte
  - Operator data: 28 bytes (4 bytes shapes + 8 bytes ratio + 8 bytes level + 4 bytes mod_a + 4 bytes mod_b)
  - mod1-4: 4 bytes
  - SynthParams begins at byte 50
  - SynthParams.write() is called with MOD_OFFSET = 2
  - This means modulators are written starting at position 50 + 2 = 52 bytes from the start

  The modulators in all three synth types actually start at the same byte position: 52!

  This explains the strange small MOD_OFFSET value of 2 for FMSynth - it's compensating for all the additional operator
   data to ensure the modulators all align at the same position.

### m8i files 22/03/25

- create a project with an imported m8i
- export this and the m8i itself 
- ask Claude to create file which creates project from M8s, then outputs concatenated binary data from version plus metadata plus instrument zero, and also m8i, in a way which will allow output to be pasted back here for interpretation
- instrument needs a read from file method in the same way that project does
- is project read from file even tested?

---

- seems like there is a 14 byte offset
- that's the same as M8 version size, noting that metadata starts at 0x0E
- feels like modulators start at a different point

### `flat` structures 22/03/25

- bake chains should be part of tooling scripts here
- but concat phrases should be part as well
- key condition is that chains are single element and have the same phrase number
- could be part of validation
- but what to call it?

### pico waveforms 08/03/25

```
(env) jhw@Justins-Air pym8 % ls /Volumes/M8/Samples/woldo/waveforms/erica\ pico 
ERICA PICO 01.wav	ERICA PICO 09.wav	ERICA PICO 17.wav	ERICA PICO 25.wav
ERICA PICO 02.wav	ERICA PICO 10.wav	ERICA PICO 18.wav	ERICA PICO 26.wav
ERICA PICO 03.wav	ERICA PICO 11.wav	ERICA PICO 19.wav	ERICA PICO 27.wav
ERICA PICO 04.wav	ERICA PICO 12.wav	ERICA PICO 20.wav	ERICA PICO 28.wav
ERICA PICO 05.wav	ERICA PICO 13.wav	ERICA PICO 21.wav	ERICA PICO 29.wav
ERICA PICO 06.wav	ERICA PICO 14.wav	ERICA PICO 22.wav	ERICA PICO 30.wav
ERICA PICO 07.wav	ERICA PICO 15.wav	ERICA PICO 23.wav	ERICA PICO 31.wav
ERICA PICO 08.wav	ERICA PICO 16.wav	ERICA PICO 24.wav	ERICA PICO 32.wav
```

### wavsynth 04/03/25

- synth params
- synth
- shapes enum
- destinations enum
- instrument FX enum
- convert hello macro to pydemo, creating both macro and wav 

### working macrosynth 03/03/25

git checkout 76008cc97879424a028a6dd78cfef28326300cdc

### class names 27/02/25

If def set_caller_module_decorator is not enabled we get the following -

```
  "phrases": {
    "__class__": "m8.api.phrases.M8Phrases",
    "items": [
      {
        "__class__": "m8.api.phrases.M8Phrase",
        "steps": [
          {
            "__class__": "m8.api.phrases.M8PhraseStep",
            "note": 36,
            "velocity": 111,
            "instrument": 0,
            "fx": [
              {
                "__class__": "m8.core.object.M8FXTuple",
                "key": 144,
                "value": 64
              }
            ]
          },
```

Paths for objects nested at leaf level are incorrect

If it is enabled, we get the following -

```
  "phrases": {
    "__class__": "m8.api.phrases.M8Phrases",
    "items": [
      {
        "__class__": "m8.api.phrases.M8Phrase",
        "steps": [
          {
            "__class__": "m8.api.phrases.M8PhraseStep",
            "note": 36,
            "velocity": 111,
            "instrument": 0,
            "fx": [
              {
                "__class__": "m8.api.phrases.cls",
                "key": 144,
                "value": 192
              }
            ]
          },
```

So now the leaf paths are correct but the class name is listed as cls!

### m8i files and JSON serialisation 25/02/25

- you might want to load trash80's synth drums and create patterns with thos
- for this you would need to load m8i files
- but you might also want to serialise those instruments to json / deserialise from json
- in the interests of transparency and of instrument modification

---

- this all starts with as_dict/as_list
- but you need to roll back enum and hex support into a new json layer which implements then as part of JSON encoders/decoders
- this layer will also need the ability to create classes from json
- and for that to work you probably need factory functions embedded in the relevat api classes

---

- roll back as_dict hex and enum support
- roll back array as_list indexation support
- check as_dict/as_list code still works but is as generic as possible
- consider renaming read as read_m8s
- new JSON serialisation layer with encoders and decoders
- factory deserialisation functions for all api classes
- convert hello macrosynth to print json

---

- extend instrument with read_m8i functions
- extend instrument with read/write_json functions

### macrosynth enums 22/02/25

- /M8/enums/instruments/macrosynth/M8MacroSynthShapes
- /M8/enums/instruments/M8FilterTypes
- /M8/enums/instruments/M8AmpLimitTypes
- /M8/enums/instruments/macrosynth/M8MacroSynthModDestinations

---

- implement above enums in M8/enums 
- include enum refs in instrument, modulator field map definitions
- refactor volume to use mod destination enum
- add low pass filter to instrument 
- add second AHD modulator for filter cutoff 
- add instrument shape
- add instrument (amp) level and limit 
- add instrument chorus
- run hello macrosynth
- check inspect_m8s shows enum keys where applicable 

### m8macro.m8s 21/02/25

```
Instrument 0: {'synth': {'type': 1, 'name': '', 'transpose': 4, 'eq': 1, 'table_tick': 1, 'volume': 0, 'pitch': 0, 'fine_tune': 128, 'shape': 0, 'timbre': 128, 'color': 128, 'degrade': 0, 'redux': 0, 'filter_type': 1, 'filter_cutoff': 48, 'filter_resonance': 160, 'amp_level': 0, 'amp_limit': 0, 'mixer_pan': 128, 'mixer_dry': 192, 'mixer_chorus': 192, 'mixer_delay': 128, 'mixer_reverb': 128}, 'modulators': [{'type': 0, 'destination': 1, 'amount': 255, 'attack': 0, 'hold': 0, 'decay': 96}, {'type': 0, 'destination': 7, 'amount': 159, 'attack': 0, 'hold': 0, 'decay': 64}]}
```

### whither enums? 21/02/25

- include enums or not?
- tried a couple of ways and neither seem ideal
- maybe enums are just syntactic sugar for the m8 interface
- as no- one can remember the underlying ints
- but the sugar format is dictated by the constraints of the interface
- if you didn't have that, maybe the api would look different?