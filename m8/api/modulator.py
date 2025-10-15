from m8.api import M8Block, split_byte, join_nibbles

# Modulator configuration
MODULATOR_BLOCK_SIZE = 6
MODULATOR_COUNT = 4

# Common field offsets (all modulator types)
TYPE_DEST_OFFSET = 0  # Combined type (high nibble) and destination (low nibble)
AMOUNT_OFFSET = 1

# Type-specific parameter offsets (from v0.3.1 config)
# AHD_ENVELOPE (type 0)
AHD_ATTACK_OFFSET = 2
AHD_HOLD_OFFSET = 3
AHD_DECAY_OFFSET = 4

# LFO (type 3)
LFO_OSCILLATOR_OFFSET = 2
LFO_TRIGGER_OFFSET = 3
LFO_FREQUENCY_OFFSET = 4

# Default values
DEFAULT_AMOUNT = 0xFF
DEFAULT_DESTINATION = 0x00
DEFAULT_AHD_DECAY = 0x80
DEFAULT_LFO_FREQUENCY = 0x10

# Default modulator configurations (mods 0,1 = AHD, mods 2,3 = LFO)
DEFAULT_MODULATOR_TYPES = [0, 0, 3, 3]

# Block sizes
BLOCK_SIZE = MODULATOR_BLOCK_SIZE
BLOCK_COUNT = MODULATOR_COUNT


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
