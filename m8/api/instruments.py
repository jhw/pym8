# m8/api/instruments.py
"""Generic M8 Instruments collection."""

from m8.api import M8Block
from m8.core.format import load_format_config

# Load configuration
config = load_format_config()

# Block sizes and counts for instruments
BLOCK_SIZE = config["instruments"]["block_size"]
BLOCK_COUNT = config["instruments"]["count"]

# Import sampler for type checking
from m8.api.sampler import M8Sampler, SAMPLER_TYPE_ID


class M8Instruments(list):
    """Collection of M8 instruments (currently only samplers)."""

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

    def is_empty(self):
        """Check if collection is empty."""
        return all(isinstance(instr, M8Block) or instr.is_empty() for instr in self)

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
