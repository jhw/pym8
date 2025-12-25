from enum import IntEnum
from m8.api import M8Block, split_byte, join_nibbles

# Modulator configuration
MODULATOR_BLOCK_SIZE = 6
MODULATOR_COUNT = 4

# Common field offsets (all modulator types)
TYPE_DEST_OFFSET = 0  # Combined type (high nibble) and destination (low nibble)
AMOUNT_OFFSET = 1

# Type-specific parameter offsets (offsets 0-1 are type/dest and amount, shared by all)
# AHD_ENVELOPE (type 0)
AHD_ATTACK_OFFSET = 2
AHD_HOLD_OFFSET = 3
AHD_DECAY_OFFSET = 4

# LFO (type 3)
LFO_OSCILLATOR_OFFSET = 2
LFO_TRIGGER_OFFSET = 3
LFO_FREQUENCY_OFFSET = 4
LFO_RETRIGGER_OFFSET = 5

# Default values
DEFAULT_AMOUNT = 0xFF
DEFAULT_DESTINATION = 0x00
DEFAULT_AHD_DECAY = 0x80
DEFAULT_LFO_FREQUENCY = 0x10

# Default modulator configurations (mods 0,1 = AHD, mods 2,3 = LFO)
# Note: Using raw integers here for backward compatibility, but M8ModulatorType enum can be used
DEFAULT_MODULATOR_TYPES = [0, 0, 3, 3]  # [AHD_ENVELOPE, AHD_ENVELOPE, LFO, LFO]

# Block sizes
BLOCK_SIZE = MODULATOR_BLOCK_SIZE
BLOCK_COUNT = MODULATOR_COUNT


# Modulator Type Enums
class M8ModulatorType(IntEnum):
    """Modulator type values (instrument-independent)."""
    AHD_ENVELOPE = 0x00     # Attack, Hold, Decay envelope
    ADSR_ENVELOPE = 0x01    # Attack, Decay, Sustain, Release envelope
    DRUM_ENVELOPE = 0x02    # Drum envelope
    LFO = 0x03              # Low-Frequency Oscillator
    TRIG_ENVELOPE = 0x04    # Trigger envelope
    TRACKING_ENVELOPE = 0x05  # Tracking envelope


class M8LFOShape(IntEnum):
    """LFO oscillator waveform shapes."""
    # Basic shapes (free-running)
    TRI = 0x00          # Triangle
    SIN = 0x01          # Sine
    RAMP_DOWN = 0x02    # Ramp down
    RAMP_UP = 0x03      # Ramp up
    EXP_DN = 0x04       # Exponential down
    EXP_UP = 0x05       # Exponential up
    SQR_DN = 0x06       # Square down
    SQR_UP = 0x07       # Square up
    RANDOM = 0x08       # Random
    DRUNK = 0x09        # Drunk walk

    # Triggered shapes
    TRI_T = 0x0A        # Triangle (triggered)
    SIN_T = 0x0B        # Sine (triggered)
    RAMPD_T = 0x0C      # Ramp down (triggered)
    RAMPU_T = 0x0D      # Ramp up (triggered)
    EXPD_T = 0x0E       # Exponential down (triggered)
    EXPU_T = 0x0F       # Exponential up (triggered)
    SQ_D_T = 0x10       # Square down (triggered)
    SQ_U_T = 0x11       # Square up (triggered)
    RAND_T = 0x12       # Random (triggered)
    DRNK_T = 0x13       # Drunk (triggered)


class M8LFOTriggerMode(IntEnum):
    """LFO trigger mode values."""
    FREE = 0x00      # Free-running
    RETRIG = 0x01    # Retrigger on note
    HOLD = 0x02      # Hold
    ONCE = 0x03      # One-shot


# Modulator Parameter Enums (type-specific parameters at offsets 2+)
# Note: Offsets 0-1 (type/dest and amount) are common to all modulator types

class M8AHDParam(IntEnum):
    """AHD Envelope parameters (Attack, Hold, Decay)."""
    ATTACK = 2
    HOLD = 3
    DECAY = 4


class M8ADSRParam(IntEnum):
    """ADSR Envelope parameters (Attack, Decay, Sustain, Release)."""
    ATTACK = 2
    DECAY = 3
    SUSTAIN = 4
    RELEASE = 5


class M8DrumParam(IntEnum):
    """Drum Envelope parameters."""
    PEAK = 2
    BODY = 3
    DECAY = 4


class M8LFOParam(IntEnum):
    """LFO parameters (Low-Frequency Oscillator)."""
    SHAPE = 2          # Oscillator waveform shape (see M8LFOShape)
    TRIGGER_MODE = 3   # Trigger mode (see M8LFOTriggerMode)
    FREQ = 4           # Frequency
    RETRIGGER = 5      # Retrigger value


class M8TrigParam(IntEnum):
    """Trigger Envelope parameters."""
    ATTACK = 2
    HOLD = 3
    DECAY = 4
    SRC = 5            # Source


class M8TrackingParam(IntEnum):
    """Tracking Envelope parameters."""
    SRC = 2            # Source
    LVAL = 3           # Low value
    HVAL = 4           # High value


class M8Modulator:
    """M8 modulator for controlling instrument parameters over time."""

    def __init__(self, mod_type=0):
        """Initialize a modulator with the given type.

        Args:
            mod_type: Modulator type (0=AHD_ENVELOPE, 3=LFO, etc.)
        """
        self._data = bytearray([0] * BLOCK_SIZE)

        # Set type in high nibble, destination in low nibble
        self._data[TYPE_DEST_OFFSET] = join_nibbles(mod_type, DEFAULT_DESTINATION)

        # Set amount default
        self._data[AMOUNT_OFFSET] = DEFAULT_AMOUNT

        # Set type-specific defaults
        if mod_type == 0:  # AHD_ENVELOPE
            self._data[AHD_DECAY_OFFSET] = DEFAULT_AHD_DECAY
        elif mod_type == 3:  # LFO
            self._data[LFO_FREQUENCY_OFFSET] = DEFAULT_LFO_FREQUENCY

    def get(self, offset):
        """Get value at offset."""
        return self._data[offset]

    def set(self, offset, value):
        """Set value at offset."""
        self._data[offset] = value & 0xFF

    @property
    def mod_type(self):
        """Get modulator type from high nibble of byte 0."""
        type_nibble, _ = split_byte(self._data[TYPE_DEST_OFFSET])
        return type_nibble

    @mod_type.setter
    def mod_type(self, value):
        """Set modulator type in high nibble of byte 0."""
        _, dest_nibble = split_byte(self._data[TYPE_DEST_OFFSET])
        self._data[TYPE_DEST_OFFSET] = join_nibbles(value, dest_nibble)

    @property
    def destination(self):
        """Get destination from low nibble of byte 0."""
        _, dest_nibble = split_byte(self._data[TYPE_DEST_OFFSET])
        return dest_nibble

    @destination.setter
    def destination(self, value):
        """Set destination in low nibble of byte 0."""
        type_nibble, _ = split_byte(self._data[TYPE_DEST_OFFSET])
        self._data[TYPE_DEST_OFFSET] = join_nibbles(type_nibble, value)

    @property
    def amount(self):
        """Get modulation amount."""
        return self._data[AMOUNT_OFFSET]

    @amount.setter
    def amount(self, value):
        """Set modulation amount."""
        self._data[AMOUNT_OFFSET] = value & 0xFF

    def write(self):
        """Convert modulator to binary data."""
        return bytes(self._data)

    def clone(self):
        """Create a copy of this modulator."""
        instance = self.__class__.__new__(self.__class__)
        instance._data = bytearray(self._data)
        return instance

    def to_dict(self, enum_mode='value'):
        """Export modulator parameters to a dictionary.

        Args:
            enum_mode: How to serialize enum values:
                      'value' (default) - use integer values
                      'name' - use enum names as strings (human-readable)

        Returns a dict with:
        - type: modulator type (int or enum name)
        - destination: destination parameter (int)
        - amount: modulation amount (int)
        - params: dict of type-specific parameters using enum names as keys
        """
        mod_type_value = self.mod_type

        result = {
            'type': M8ModulatorType(mod_type_value).name if enum_mode == 'name' else mod_type_value,
            'destination': self.destination,
            'amount': self.amount,
            'params': {}
        }

        # Mapping of LFO parameters to their enum types (for human-readable mode)
        lfo_param_enum_types = {
            'SHAPE': M8LFOShape,
            'TRIGGER_MODE': M8LFOTriggerMode,
        }

        # Add type-specific parameters based on modulator type
        if mod_type_value == M8ModulatorType.AHD_ENVELOPE:
            for param in M8AHDParam:
                result['params'][param.name] = self.get(param)
        elif mod_type_value == M8ModulatorType.ADSR_ENVELOPE:
            for param in M8ADSRParam:
                result['params'][param.name] = self.get(param)
        elif mod_type_value == M8ModulatorType.DRUM_ENVELOPE:
            for param in M8DrumParam:
                result['params'][param.name] = self.get(param)
        elif mod_type_value == M8ModulatorType.LFO:
            for param in M8LFOParam:
                value = self.get(param)
                # Convert enum values to names if requested
                if enum_mode == 'name' and param.name in lfo_param_enum_types:
                    try:
                        enum_type = lfo_param_enum_types[param.name]
                        value = enum_type(value).name
                    except (ValueError, KeyError):
                        # If value doesn't map to enum, keep as integer
                        pass
                result['params'][param.name] = value
        elif mod_type_value == M8ModulatorType.TRIG_ENVELOPE:
            for param in M8TrigParam:
                result['params'][param.name] = self.get(param)
        elif mod_type_value == M8ModulatorType.TRACKING_ENVELOPE:
            for param in M8TrackingParam:
                result['params'][param.name] = self.get(param)

        return result

    @classmethod
    def from_dict(cls, params):
        """Create a modulator from a parameter dictionary.

        Args:
            params: Dict with keys: type, destination, amount, params
                   - type can be int, M8ModulatorType enum value, or string name
                   - params is a dict with parameter names as keys

        Returns:
            M8Modulator instance configured with given parameters
        """
        mod_type = params.get('type', 0)

        # Handle string enum names (e.g., 'AHD_ENVELOPE')
        if isinstance(mod_type, str):
            try:
                mod_type = M8ModulatorType[mod_type].value
            except KeyError:
                # Unknown type name, default to 0
                mod_type = 0

        # Create modulator with specified type
        instance = cls(mod_type=mod_type)

        # Set common parameters
        if 'destination' in params:
            instance.destination = params['destination']
        if 'amount' in params:
            instance.amount = params['amount']

        # Set type-specific parameters
        type_params = params.get('params', {})
        if not type_params:
            return instance

        # Mapping of LFO parameters to their enum types (for string value parsing)
        lfo_param_enum_types = {
            'SHAPE': M8LFOShape,
            'TRIGGER_MODE': M8LFOTriggerMode,
        }

        # Map parameter names to enum values based on type
        param_enum = None
        if mod_type == M8ModulatorType.AHD_ENVELOPE:
            param_enum = M8AHDParam
        elif mod_type == M8ModulatorType.ADSR_ENVELOPE:
            param_enum = M8ADSRParam
        elif mod_type == M8ModulatorType.DRUM_ENVELOPE:
            param_enum = M8DrumParam
        elif mod_type == M8ModulatorType.LFO:
            param_enum = M8LFOParam
        elif mod_type == M8ModulatorType.TRIG_ENVELOPE:
            param_enum = M8TrigParam
        elif mod_type == M8ModulatorType.TRACKING_ENVELOPE:
            param_enum = M8TrackingParam

        if param_enum:
            for param_name, value in type_params.items():
                # Try to get enum member by name
                try:
                    param_offset = param_enum[param_name]

                    # Handle string enum names for LFO parameters
                    if mod_type == M8ModulatorType.LFO and isinstance(value, str) and param_name in lfo_param_enum_types:
                        try:
                            enum_type = lfo_param_enum_types[param_name]
                            value = enum_type[value].value
                        except KeyError:
                            # Unknown enum name, skip
                            continue

                    instance.set(param_offset, value)
                except KeyError:
                    # Skip unknown parameter names
                    pass

        return instance

    @classmethod
    def read(cls, data):
        """Read modulator from binary data."""
        instance = cls.__new__(cls)
        instance._data = bytearray(data[:BLOCK_SIZE])
        return instance


class M8Modulators(list):
    """Collection of 4 modulators for an M8 instrument."""

    def __init__(self):
        super().__init__()
        # Initialize with default modulators (2 AHD, 2 LFO)
        for mod_type in DEFAULT_MODULATOR_TYPES:
            self.append(M8Modulator(mod_type))

    @classmethod
    def read(cls, data):
        instance = cls.__new__(cls)
        list.__init__(instance)

        for i in range(BLOCK_COUNT):
            start = i * BLOCK_SIZE
            block_data = data[start:start + BLOCK_SIZE]

            if len(block_data) < BLOCK_SIZE:
                # Pad with zeros if insufficient data
                block_data = block_data + bytes([0] * (BLOCK_SIZE - len(block_data)))

            instance.append(M8Modulator.read(block_data))

        return instance

    def clone(self):
        instance = self.__class__()
        instance.clear()

        for mod in self:
            instance.append(mod.clone())

        return instance

    def to_dict(self, enum_mode='value'):
        """Export all modulators to a list of dictionaries.

        Args:
            enum_mode: How to serialize enum values ('value' or 'name')
        """
        return [mod.to_dict(enum_mode=enum_mode) for mod in self]

    @classmethod
    def from_dict(cls, modulators_list):
        """Create modulators collection from a list of parameter dicts.

        Args:
            modulators_list: List of dicts, each containing modulator params

        Returns:
            M8Modulators instance with configured modulators
        """
        instance = cls.__new__(cls)
        list.__init__(instance)

        for mod_params in modulators_list:
            instance.append(M8Modulator.from_dict(mod_params))

        # Pad to 4 modulators if needed
        while len(instance) < BLOCK_COUNT:
            instance.append(M8Modulator())

        return instance

    def write(self):
        result = bytearray()
        for mod in self:
            mod_data = mod.write()

            # Ensure each modulator occupies exactly BLOCK_SIZE bytes
            if len(mod_data) < BLOCK_SIZE:
                mod_data = mod_data + bytes([0x0] * (BLOCK_SIZE - len(mod_data)))
            elif len(mod_data) > BLOCK_SIZE:
                mod_data = mod_data[:BLOCK_SIZE]

            result.extend(mod_data)

        return bytes(result)
