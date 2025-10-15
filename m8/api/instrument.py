# m8/api/instrument.py
"""Base instrument class for all M8 instruments."""

from m8.api import _read_fixed_string, _write_fixed_string
from m8.api.version import M8Version
from m8.api.modulator import M8Modulators

# Common instrument configuration
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
