# m8/api/instruments/sampler.py
"""Simplified M8 Sampler instrument - the only instrument type supported."""

from m8.api import M8Block, read_fixed_string, write_fixed_string
from m8.api.instruments.base import M8InstrumentBase
from m8.config import load_format_config

# Load configuration
config = load_format_config()

# Block sizes and counts for instruments
BLOCK_SIZE = config["instruments"]["block_size"]
BLOCK_COUNT = config["instruments"]["count"]

# Sampler configuration
SAMPLER_CONFIG = config["instruments"]["types"]["SAMPLER"]
SAMPLER_TYPE_ID = SAMPLER_CONFIG["type_id"]


class M8InstrumentParams:
    """Sampler-specific parameters."""

    def __init__(self, play_mode=0, slice=0, sample_path=""):
        self.play_mode = play_mode
        self.slice = slice
        self.sample_path = sample_path

    def read(self, data):
        """Read parameters from binary data."""
        self.play_mode = data[SAMPLER_CONFIG["params"]["play_mode"]["offset"]]
        self.slice = data[SAMPLER_CONFIG["params"]["slice"]["offset"]]

        # Read sample_path
        sample_path_config = SAMPLER_CONFIG["sample_path"]
        offset = sample_path_config["offset"]
        size = sample_path_config["size"]
        self.sample_path = read_fixed_string(data, offset, size)

    def write(self):
        """Write parameters to binary data."""
        # Calculate buffer size needed
        sample_path_config = SAMPLER_CONFIG["sample_path"]
        max_offset = sample_path_config["offset"] + sample_path_config["size"]

        buffer = bytearray([0] * max_offset)

        buffer[SAMPLER_CONFIG["params"]["play_mode"]["offset"]] = self.play_mode & 0xFF
        buffer[SAMPLER_CONFIG["params"]["slice"]["offset"]] = self.slice & 0xFF

        # Write sample_path
        offset = sample_path_config["offset"]
        size = sample_path_config["size"]
        buffer[offset:offset + size] = write_fixed_string(self.sample_path, size)

        return bytes(buffer)

    def clone(self):
        """Create a copy of this params object."""
        return M8InstrumentParams(
            play_mode=self.play_mode,
            slice=self.slice,
            sample_path=self.sample_path
        )

    def as_dict(self):
        """Convert to dictionary."""
        return {
            "play_mode": self.play_mode,
            "slice": self.slice,
            "sample_path": self.sample_path
        }

    @classmethod
    def from_dict(cls, data):
        """Create from dictionary."""
        return cls(
            play_mode=data.get("play_mode", 0),
            slice=data.get("slice", 0),
            sample_path=data.get("sample_path", "")
        )


class M8Sampler(M8InstrumentBase):
    """M8 Sampler instrument - the only instrument type supported."""

    def __init__(self, name="", sample_path="", play_mode=0, slice=0,
                 volume=255, pitch=64, transpose=4, eq=1, table_tick=1, finetune=128):
        """Initialize a sampler instrument with default parameters."""
        # Initialize base class with common parameters
        super().__init__(name=name, volume=volume, pitch=pitch, transpose=transpose,
                        eq=eq, table_tick=table_tick, finetune=finetune)

        # Type is always SAMPLER
        self.type = SAMPLER_TYPE_ID

        # Sampler-specific parameters
        self.params = M8InstrumentParams(play_mode, slice, sample_path)

    def write(self):
        """Convert instrument to binary data."""
        buffer = bytearray([0] * BLOCK_SIZE)

        # Write type
        buffer[self.TYPE_OFFSET] = SAMPLER_TYPE_ID

        # Write common parameters using base class method
        self._write_common_parameters(buffer)

        # Write sampler-specific parameters - write each field at its offset
        buffer[SAMPLER_CONFIG["params"]["play_mode"]["offset"]] = self.params.play_mode & 0xFF
        buffer[SAMPLER_CONFIG["params"]["slice"]["offset"]] = self.params.slice & 0xFF

        # Write sample_path
        sample_path_config = SAMPLER_CONFIG["sample_path"]
        offset = sample_path_config["offset"]
        size = sample_path_config["size"]
        sample_path_bytes = write_fixed_string(self.params.sample_path, size)
        buffer[offset:offset + size] = sample_path_bytes

        return bytes(buffer)

    def is_empty(self):
        """Check if instrument is empty."""
        return self.type != SAMPLER_TYPE_ID

    def clone(self):
        """Create a copy of this instrument."""
        instance = M8Sampler(
            name=self.name,
            sample_path=self.params.sample_path,
            play_mode=self.params.play_mode,
            slice=self.params.slice,
            volume=self.volume,
            pitch=self.pitch,
            transpose=self.transpose,
            eq=self.eq,
            table_tick=self.table_tick,
            finetune=self.finetune
        )
        instance.version = self.version
        return instance

    def as_dict(self):
        """Convert to dictionary."""
        result = {
            "type": self.type,
            "name": self.name,
            "volume": self.volume,
            "pitch": self.pitch,
            "transpose": self.transpose,
            "eq": self.eq,
            "table_tick": self.table_tick,
            "finetune": self.finetune
        }

        # Add params
        params_dict = self.params.as_dict()
        result.update(params_dict)

        return result

    @classmethod
    def from_dict(cls, data):
        """Create instrument from dictionary."""
        return cls(
            name=data.get("name", ""),
            sample_path=data.get("sample_path", ""),
            play_mode=data.get("play_mode", 0),
            slice=data.get("slice", 0),
            volume=data.get("volume", 255),
            pitch=data.get("pitch", 64),
            transpose=data.get("transpose", 4),
            eq=data.get("eq", 1),
            table_tick=data.get("table_tick", 1),
            finetune=data.get("finetune", 128)
        )

    @classmethod
    def read(cls, data):
        """Read instrument from binary data."""
        instrument = cls()
        instrument._read_common_parameters(data)
        instrument.params.read(data)
        return instrument



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
        instance = cls.__new__(cls)
        list.__init__(instance)

        for i in range(BLOCK_COUNT):
            start = i * BLOCK_SIZE
            block_data = data[start:start + BLOCK_SIZE]

            # Check if it's a sampler instrument
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

    def as_list(self):
        """Convert to list for serialization."""
        items = []
        for i, instr in enumerate(self):
            if not (isinstance(instr, M8Block) or instr.is_empty()):
                item_dict = instr.as_dict()
                item_dict["index"] = i
                items.append(item_dict)

        return items

    @classmethod
    def from_list(cls, items):
        """Create collection from list."""
        instance = cls.__new__(cls)
        list.__init__(instance)

        # Initialize with empty blocks
        for _ in range(BLOCK_COUNT):
            instance.append(M8Block())

        # Set instruments at their positions
        if items:
            for instr_data in items:
                index = instr_data.get("index", 0)
                if 0 <= index < BLOCK_COUNT:
                    instr_dict = {k: v for k, v in instr_data.items() if k != "index"}
                    instance[index] = M8Sampler.from_dict(instr_dict)

        return instance
