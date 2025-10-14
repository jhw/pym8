# m8/api/sampler.py
"""M8 Sampler instrument - the only instrument type supported."""

from m8.api import M8Block, _read_fixed_string, _write_fixed_string
from m8.api.version import M8Version

# Instruments configuration (from instruments.py to avoid circular import)
INSTRUMENTS_BLOCK_SIZE = 215
INSTRUMENTS_COUNT = 128

# Sampler configuration
SAMPLER_TYPE_ID = 2

# Common field offsets
TYPE_OFFSET = 0
NAME_OFFSET = 1
NAME_LENGTH = 12

# Sample path configuration
SAMPLE_PATH_OFFSET = 87
SAMPLE_PATH_SIZE = 128

# Sampler parameter offsets (from v0.3.1 format config)
FINETUNE_OFFSET = 17      # Common field, default: 0x80 (128)
LENGTH_OFFSET = 22        # Sample length, default: 0xFF (255)
CUTOFF_OFFSET = 25        # Filter cutoff, default: 0xFF (255)
PAN_OFFSET = 29           # Amp/mixer pan, default: 0x80 (128)
DRY_OFFSET = 30           # Amp/mixer dry, default: 0xC0 (192)

# Default values for parameters with non-zero defaults
DEFAULT_FINETUNE = 0x80   # 128
DEFAULT_LENGTH = 0xFF     # 255
DEFAULT_CUTOFF = 0xFF     # 255
DEFAULT_PAN = 0x80        # 128
DEFAULT_DRY = 0xC0        # 192

# Block sizes and counts for samplers
BLOCK_SIZE = INSTRUMENTS_BLOCK_SIZE
BLOCK_COUNT = INSTRUMENTS_COUNT


class M8Sampler:
    """M8 Sampler instrument - the only instrument type supported."""

    def __init__(self, name="", sample_path="", length=DEFAULT_LENGTH, finetune=DEFAULT_FINETUNE,
                 cutoff=DEFAULT_CUTOFF, pan=DEFAULT_PAN, dry=DEFAULT_DRY):
        """Initialize a sampler instrument with default parameters."""
        # Type is always SAMPLER
        self.type = SAMPLER_TYPE_ID

        # Version (set from project or file)
        self.version = M8Version()

        # Common parameters
        self.name = name

        # Sampler-specific parameters
        self.sample_path = sample_path
        self.length = length
        self.finetune = finetune
        self.cutoff = cutoff
        self.pan = pan
        self.dry = dry

    def write(self):
        """Convert instrument to binary data."""
        buffer = bytearray([0] * BLOCK_SIZE)

        # Write type
        buffer[TYPE_OFFSET] = SAMPLER_TYPE_ID

        # Write name
        name_bytes = _write_fixed_string(self.name, NAME_LENGTH)
        buffer[NAME_OFFSET:NAME_OFFSET + NAME_LENGTH] = name_bytes

        # Write parameters with non-zero defaults
        buffer[FINETUNE_OFFSET] = self.finetune & 0xFF
        buffer[LENGTH_OFFSET] = self.length & 0xFF
        buffer[CUTOFF_OFFSET] = self.cutoff & 0xFF
        buffer[PAN_OFFSET] = self.pan & 0xFF
        buffer[DRY_OFFSET] = self.dry & 0xFF

        # Write sample_path
        sample_path_bytes = _write_fixed_string(self.sample_path, SAMPLE_PATH_SIZE)
        buffer[SAMPLE_PATH_OFFSET:SAMPLE_PATH_OFFSET + SAMPLE_PATH_SIZE] = sample_path_bytes

        return bytes(buffer)

    def clone(self):
        """Create a copy of this instrument."""
        instance = M8Sampler(
            name=self.name,
            sample_path=self.sample_path,
            length=self.length,
            finetune=self.finetune,
            cutoff=self.cutoff,
            pan=self.pan,
            dry=self.dry
        )
        instance.version = self.version
        return instance

    @classmethod
    def read(cls, data):
        """Read instrument from binary data."""
        instrument = cls()
        instrument.type = data[TYPE_OFFSET]
        instrument.name = _read_fixed_string(data, NAME_OFFSET, NAME_LENGTH)
        instrument.finetune = data[FINETUNE_OFFSET]
        instrument.length = data[LENGTH_OFFSET]
        instrument.cutoff = data[CUTOFF_OFFSET]
        instrument.pan = data[PAN_OFFSET]
        instrument.dry = data[DRY_OFFSET]
        instrument.sample_path = _read_fixed_string(data, SAMPLE_PATH_OFFSET, SAMPLE_PATH_SIZE)
        return instrument
