# m8/api/instrument.py
"""M8 Instrument classes - base class and collection."""

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


class M8Instrument:
    """Base class for all M8 instrument types.

    Handles common functionality:
    - Type byte at offset 0
    - Name at offsets 1-12
    - Modulators at offset 63
    - Version tracking
    - Binary buffer management (_data)
    """

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


class M8Instruments(list):
    """Collection of M8 instruments."""

    def __init__(self, items=None):
        """Initialize collection with optional instruments."""
        super().__init__()
        items = items or []

        for item in items:
            self.append(item)

        # Fill remaining slots with empty blocks
        while len(self) < BLOCK_COUNT:
            self.append(M8Block())

    @classmethod
    def read(cls, data):
        """Read instruments from binary data."""
        from m8.api.sampler import M8Sampler, SAMPLER_TYPE_ID
        
        instance = cls.__new__(cls)
        list.__init__(instance)

        for i in range(BLOCK_COUNT):
            start = i * BLOCK_SIZE
            block_data = data[start:start + BLOCK_SIZE]

            # Check instrument type
            instr_type = block_data[0]
            if instr_type == SAMPLER_TYPE_ID:
                instance.append(M8Sampler.read(block_data))
            else:
                # Empty slot
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
