# m8/api/instrument.py
"""M8 Instrument classes - base class and collection."""

from enum import IntEnum
from m8.api import M8Block, _read_fixed_string, _write_fixed_string
from m8.api.version import M8Version
from m8.api.modulator import M8Modulators

# Common instrument configuration
INSTRUMENTS_OFFSET = 80446
INSTRUMENTS_BLOCK_SIZE = 215
INSTRUMENTS_COUNT = 128

# Common field offsets (shared by all instrument types)
TYPE_OFFSET = 0
NAME_OFFSET = 1
NAME_LENGTH = 12
MODULATORS_OFFSET = 63

# Block sizes
BLOCK_SIZE = INSTRUMENTS_BLOCK_SIZE
BLOCK_COUNT = INSTRUMENTS_COUNT


# Common Parameter Value Enums (shared across instrument types)
class M8FilterType(IntEnum):
    """Filter type values (common across all synthesizer instruments)."""
    OFF = 0x00       # No filter
    LOWPASS = 0x01   # Low pass filter
    HIGHPASS = 0x02  # High pass filter
    BANDPASS = 0x03  # Band pass filter
    BANDSTOP = 0x04  # Band stop filter
    LP_HP = 0x05     # LP > HP filter
    ZDF_LP = 0x06    # Zero-delay feedback low pass
    ZDF_HP = 0x07    # Zero-delay feedback high pass


class M8LimiterType(IntEnum):
    """Limiter/clipping type values (common across all synthesizer instruments)."""
    CLIP = 0x00      # Hard clipping
    SIN = 0x01       # Sine wave limiting
    FOLD = 0x02      # Wave folding
    WRAP = 0x03      # Wave wrapping
    POST = 0x04      # Post-processing limiter
    POSTAD = 0x05    # Post-processing with adaptive limiting
    POST_W1 = 0x06   # Post-processing variant 1
    POST_W2 = 0x07   # Post-processing variant 2
    POST_W3 = 0x08   # Post-processing variant 3


class M8Instrument:
    """Base class for all M8 instrument types.

    Handles common functionality:
    - Type byte at offset 0
    - Name at offsets 1-12
    - Modulators at offset 63
    - Version tracking
    - Binary buffer management (_data)
    - Generic dict serialization (to_dict/from_dict)

    Subclasses should define:
    - PARAM_ENUM_CLASS: The parameter enum class (e.g., M8WavsynthParam)
    - PARAM_ENUM_TYPES: Dict mapping parameter names to their enum types
    - EXTRA_FIELDS: List of additional dict fields beyond 'name' and 'params'
    """

    # Subclasses should override these
    PARAM_ENUM_CLASS = None
    PARAM_ENUM_TYPES = {}
    EXTRA_FIELDS = []

    def __init__(self, instrument_type_id, block_size=BLOCK_SIZE):
        """Initialize instrument with type and buffer.

        Args:
            instrument_type_id: Instrument type ID (e.g., 2 for sampler)
            block_size: Size of binary buffer (default 215)
        """
        # Initialize buffer with zeros
        self._data = bytearray([0] * block_size)

        # Set type
        self._data[TYPE_OFFSET] = instrument_type_id

        # Version (set from project or file)
        self.version = M8Version()

        # Initialize modulators (4 modulators: 2 AHD, 2 LFO)
        self.modulators = M8Modulators()

    def get(self, offset):
        """Get parameter value at offset."""
        return self._data[offset]

    def set(self, offset, value):
        """Set parameter value at offset."""
        self._data[offset] = value & 0xFF

    def _apply_defaults(self, defaults):
        """Apply default parameter values.

        Args:
            defaults: List of (offset, value) tuples
        """
        for offset, value in defaults:
            self._data[offset] = value

    @property
    def name(self):
        """Get instrument name."""
        return _read_fixed_string(self._data, NAME_OFFSET, NAME_LENGTH)

    @name.setter
    def name(self, value):
        """Set instrument name."""
        name_bytes = _write_fixed_string(value, NAME_LENGTH)
        self._data[NAME_OFFSET:NAME_OFFSET + NAME_LENGTH] = name_bytes

    def write(self):
        """Convert instrument to binary data.

        Subclasses should override if they need custom write logic,
        but should call super().write() to get the base buffer.
        """
        buffer = bytearray(self._data)

        # Write modulators at offset 63
        modulator_data = self.modulators.write()
        buffer[MODULATORS_OFFSET:MODULATORS_OFFSET + len(modulator_data)] = modulator_data

        return bytes(buffer)

    def clone(self):
        """Create a copy of this instrument.

        Subclasses should override this to use their own class.
        """
        instance = self.__class__.__new__(self.__class__)
        instance._data = bytearray(self._data)
        instance.version = self.version
        instance.modulators = self.modulators.clone()
        return instance

    @classmethod
    def read(cls, data):
        """Read instrument from binary data.

        Subclasses should override this to handle their specific initialization.
        """
        instance = cls.__new__(cls)
        instance._data = bytearray(data[:BLOCK_SIZE])
        instance.version = M8Version()

        # Read modulators from offset 63
        instance.modulators = M8Modulators.read(data[MODULATORS_OFFSET:])

        return instance

    def _get_extra_dict_fields(self):
        """Get extra fields for dict export (subclasses can override).

        Returns:
            Dict with additional fields beyond 'name', 'params', 'modulators'
        """
        return {}

    def _set_extra_dict_fields(self, fields):
        """Set extra fields from dict import (subclasses can override).

        Args:
            fields: Dict with additional fields
        """
        pass

    def to_dict(self, enum_mode='value'):
        """Export instrument parameters to a dictionary.

        Args:
            enum_mode: How to serialize enum values:
                      'value' (default) - use integer values
                      'name' - use enum names as strings (human-readable)

        Returns a dict with:
        - name: instrument name
        - params: dict of instrument parameters using param enum names as keys
        - modulators: list of modulator parameter dicts
        - (additional fields from _get_extra_dict_fields)
        """
        if self.PARAM_ENUM_CLASS is None:
            raise NotImplementedError(
                f"{self.__class__.__name__} must define PARAM_ENUM_CLASS"
            )

        result = {
            'name': self.name,
            'params': {},
            'modulators': self.modulators.to_dict(enum_mode=enum_mode)
        }

        # Add any extra fields from subclass
        result.update(self._get_extra_dict_fields())

        # Export all parameters (excluding TYPE and NAME which are handled separately)
        for param in self.PARAM_ENUM_CLASS:
            param_name = param.name
            if param_name in ('TYPE', 'NAME'):
                continue

            value = self.get(param)

            # Convert enum values to names if requested
            if enum_mode == 'name' and param_name in self.PARAM_ENUM_TYPES:
                try:
                    enum_type = self.PARAM_ENUM_TYPES[param_name]
                    value = enum_type(value).name
                except (ValueError, KeyError):
                    # If value doesn't map to enum, keep as integer
                    pass

            result['params'][param_name] = value

        return result

    @classmethod
    def from_dict(cls, params):
        """Create an instrument from a parameter dictionary.

        Args:
            params: Dict with keys: name, params, modulators
                   - params is a dict with parameter names as keys
                   - param values can be integers or enum names (strings)
                   - modulators is a list of modulator parameter dicts

        Returns:
            Instrument instance configured with given parameters
        """
        if cls.PARAM_ENUM_CLASS is None:
            raise NotImplementedError(
                f"{cls.__name__} must define PARAM_ENUM_CLASS"
            )

        # Extract basic fields
        name = params.get('name', '')

        # Create instance with basic parameters
        # Subclasses will handle their specific __init__ parameters
        instance = cls._create_from_dict(params)
        instance.name = name

        # Set extra fields (like sample_path for sampler)
        instance._set_extra_dict_fields(params)

        # Apply parameter overrides
        instrument_params = params.get('params', {})
        for param_name, value in instrument_params.items():
            try:
                param_offset = cls.PARAM_ENUM_CLASS[param_name]

                # Handle string enum names
                if isinstance(value, str) and param_name in cls.PARAM_ENUM_TYPES:
                    try:
                        enum_type = cls.PARAM_ENUM_TYPES[param_name]
                        value = enum_type[value].value
                    except KeyError:
                        # Unknown enum name, skip
                        continue

                instance.set(param_offset, value)
            except KeyError:
                # Skip unknown parameter names
                pass

        # Apply modulator configuration
        modulators_list = params.get('modulators')
        if modulators_list:
            instance.modulators = M8Modulators.from_dict(modulators_list)

        return instance

    @classmethod
    def _create_from_dict(cls, params):
        """Create instance for from_dict (subclasses can override).

        Args:
            params: Full params dict

        Returns:
            New instance of the class
        """
        # Default: just call constructor with name
        return cls(name=params.get('name', ''))


class M8Instruments(list):
    """Collection of M8 instruments."""

    def __init__(self, items=None):
        """Initialize collection with optional instruments."""
        super().__init__()
        items = items or []

        for item in items:
            self.append(item)

        # Fill remaining slots with empty instrument blocks (type 0xFF)
        while len(self) < BLOCK_COUNT:
            empty_block = M8Block()
            empty_block.data = bytearray([0xFF] + [0] * (BLOCK_SIZE - 1))
            self.append(empty_block)

    @classmethod
    def read(cls, data):
        """Read instruments from binary data."""
        from m8.api.instruments.sampler import M8Sampler, SAMPLER_TYPE_ID
        from m8.api.instruments.wavsynth import M8Wavsynth, WAVSYNTH_TYPE_ID
        from m8.api.instruments.macrosynth import M8Macrosynth, MACROSYNTH_TYPE_ID

        instance = cls.__new__(cls)
        list.__init__(instance)

        for i in range(BLOCK_COUNT):
            start = i * BLOCK_SIZE
            block_data = data[start:start + BLOCK_SIZE]

            # Check instrument type
            instr_type = block_data[0]
            if instr_type == WAVSYNTH_TYPE_ID:
                instance.append(M8Wavsynth.read(block_data))
            elif instr_type == MACROSYNTH_TYPE_ID:
                instance.append(M8Macrosynth.read(block_data))
            elif instr_type == SAMPLER_TYPE_ID:
                instance.append(M8Sampler.read(block_data))
            elif instr_type == 0xFF:
                # Empty slot
                instance.append(M8Block.read(block_data))
            else:
                # Unknown instrument type - treat as empty
                instance.append(M8Block.read(block_data))

        return instance

    def clone(self):
        """Create a copy of this collection."""
        instance = self.__class__.__new__(self.__class__)
        list.__init__(instance)

        for instr in self:
            if hasattr(instr, 'clone'):
                instance.append(instr.clone())
            else:
                instance.append(instr)

        return instance

    def write(self):
        """Write instruments to binary data."""
        result = bytearray()

        for instr in self:
            instr_data = instr.write() if hasattr(instr, 'write') else bytes([0] * BLOCK_SIZE)

            # Ensure exactly BLOCK_SIZE bytes
            if len(instr_data) < BLOCK_SIZE:
                instr_data = instr_data + bytes([0] * (BLOCK_SIZE - len(instr_data)))
            elif len(instr_data) > BLOCK_SIZE:
                instr_data = instr_data[:BLOCK_SIZE]

            result.extend(instr_data)

        return bytes(result)
