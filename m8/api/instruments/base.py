# m8/api/instruments/base.py
"""Base class for M8 instruments."""

from m8.api import read_fixed_string, write_fixed_string
from m8.api.version import M8Version
from m8.config import load_format_config, get_offset

# Load configuration
config = load_format_config()

# Common parameter offsets from config
common_fields = config["instruments"]["common_fields"]

TYPE_OFFSET = common_fields["type"]["offset"]
NAME_OFFSET = common_fields["name"]["offset"]
NAME_LENGTH = common_fields["name"]["size"]
VOLUME_OFFSET = common_fields["volume"]["offset"]
PITCH_OFFSET = common_fields["pitch"]["offset"]
FINETUNE_OFFSET = common_fields["finetune"]["offset"]
TABLE_TICK_OFFSET = common_fields["table_tick"]["offset"]
TRANSPOSE_EQ_OFFSET = common_fields["transpose_eq"]["offset"]


class M8InstrumentBase:
    """Base class for M8 instruments with common parameters."""

    TYPE_OFFSET = TYPE_OFFSET
    NAME_OFFSET = NAME_OFFSET
    NAME_LENGTH = NAME_LENGTH
    VOLUME_OFFSET = VOLUME_OFFSET
    PITCH_OFFSET = PITCH_OFFSET
    FINETUNE_OFFSET = FINETUNE_OFFSET
    TABLE_TICK_OFFSET = TABLE_TICK_OFFSET
    TRANSPOSE_EQ_OFFSET = TRANSPOSE_EQ_OFFSET

    def __init__(self, name="", volume=255, pitch=64, transpose=4, eq=1, table_tick=1, finetune=128):
        """Initialize common instrument parameters."""
        # Version (set from project or file)
        self.version = M8Version()

        # Common parameters
        self.name = name
        self.volume = volume
        self.pitch = pitch
        self.transpose = transpose
        self.eq = eq
        self.table_tick = table_tick
        self.finetune = finetune

    def _read_common_parameters(self, data):
        """Read common parameters from binary data."""
        self.type = data[self.TYPE_OFFSET]
        self.name = read_fixed_string(data, self.NAME_OFFSET, self.NAME_LENGTH)

        # Read transpose and eq from combined byte
        combined_byte = data[self.TRANSPOSE_EQ_OFFSET]
        self.transpose = combined_byte & 0x0F
        self.eq = (combined_byte >> 4) & 0x0F

        self.table_tick = data[self.TABLE_TICK_OFFSET]
        self.volume = data[self.VOLUME_OFFSET]
        self.pitch = data[self.PITCH_OFFSET]
        self.finetune = data[self.FINETUNE_OFFSET]

    def _write_common_parameters(self, buffer):
        """Write common parameters to binary buffer."""
        # Write name
        name_bytes = write_fixed_string(self.name, self.NAME_LENGTH)
        buffer[self.NAME_OFFSET:self.NAME_OFFSET + self.NAME_LENGTH] = name_bytes

        # Write transpose and eq combined
        buffer[self.TRANSPOSE_EQ_OFFSET] = (self.transpose & 0x0F) | ((self.eq & 0x0F) << 4)

        # Write other common parameters
        buffer[self.TABLE_TICK_OFFSET] = self.table_tick & 0xFF
        buffer[self.VOLUME_OFFSET] = self.volume & 0xFF
        buffer[self.PITCH_OFFSET] = self.pitch & 0xFF
        buffer[self.FINETUNE_OFFSET] = self.finetune & 0xFF

    @classmethod
    def read_from_file(cls, file_path):
        """Read instrument from .m8i file."""
        with open(file_path, "rb") as f:
            data = f.read()

        # Read version
        version_offset = get_offset("version")
        version = M8Version.read(data[version_offset:])

        # Read instrument data
        metadata_offset = get_offset("metadata")
        instrument_data = data[metadata_offset:]

        instrument = cls.read(instrument_data)
        instrument.version = version

        return instrument

    def write_to_file(self, file_path):
        """Write instrument to .m8i file."""
        import os

        # Create directory if needed
        directory = os.path.dirname(file_path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)

        instrument_data = self.write()

        # Get offsets
        version_offset = get_offset("version")
        metadata_offset = get_offset("metadata")

        # Create file buffer
        m8i_data = bytearray([0] * metadata_offset) + instrument_data

        # Write version
        version_data = self.version.write()
        m8i_data[version_offset:version_offset + len(version_data)] = version_data

        with open(file_path, "wb") as f:
            f.write(m8i_data)
