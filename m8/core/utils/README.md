# M8 API Utilities

This directory contains utility modules that provide common functionality used across the M8 API.

## `enums.py`

The `enums.py` module centralizes all enum-related functionality for improved reusability and easier maintenance. It provides utilities for:

- Converting between string enum names and numeric enum values
- Supporting instrument-specific enum mappings
- Dynamically loading enum classes from paths
- Handling enum properties in classes
- Serializing and deserializing enum values for JSON

### Key Features

1. **Generic Enum Functions**: Basic conversion between enum values and names
   - `serialize_enum()` - Convert an enum value to its string name
   - `deserialize_enum()` - Convert a string to its corresponding enum value

2. **Instrument-Specific Enum Support**: 
   - `get_enum_paths_for_instrument()` - Get enum paths specific to an instrument type
   - `load_enum_classes()` - Dynamically load enum classes from paths

3. **Parameter-Level Enum Functions**:
   - `serialize_param_enum_value()` - Convert a parameter value to its enum string representation
   - `deserialize_param_enum()` - Convert a string parameter value to its numeric enum value
   - `ensure_enum_int_value()` - Ensure a value is an integer enum value

4. **Enum Property Support**:
   - `EnumPropertyMixin` - Mixin class to add enum support to class properties

5. **Utility Functions**:
   - `get_enum_names()` - Get all valid enum names for a class
   - `get_enum_values()` - Get all valid enum values for a class
   - `enum_name_to_value()` - Convert a name to its value
   - `enum_value_to_name()` - Convert a value to its name

### Usage Example

```python
from m8.api.utils.enums import serialize_enum, deserialize_enum
from m8.enums import M8FilterTypes

# Convert enum value to string
filter_name = serialize_enum(M8FilterTypes.LOWPASS)  # "LOWPASS"

# Convert string to enum value
filter_value = deserialize_enum(M8FilterTypes, "BANDPASS")  # 3
```

For working with instrument-specific enums:

```python
from m8.api.utils.enums import deserialize_param_enum

# Convert string enum to value for a specific instrument
wavsynth_cutoff = deserialize_param_enum(
    ["m8.enums.wavsynth.M8WavSynthModDestinations"],
    "CUTOFF",
    "destination",
    instrument_type=0x00
)
```

Using the enum property mixin:

```python
from m8.api.utils.enums import EnumPropertyMixin
from m8.enums import M8FilterTypes

class MyClass(EnumPropertyMixin):
    ENUM_MAPPINGS = {
        'filter_type': {'enum_class': M8FilterTypes}
    }
    
    def __init__(self):
        self._filter_type = M8FilterTypes.LOWPASS.value
    
    @property
    def filter_type(self):
        return self._get_enum_name('filter_type', self._filter_type)
    
    @filter_type.setter
    def filter_type(self, value):
        self._filter_type = self._get_enum_value('filter_type', value)

# Use with string or int values
obj = MyClass()
obj.filter_type = "BANDPASS"  # Sets to M8FilterTypes.BANDPASS.value (3)
print(obj.filter_type)        # "BANDPASS"
```