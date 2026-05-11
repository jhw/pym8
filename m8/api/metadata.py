# m8/api/metadata.py
"""M8 project metadata — directory, tempo, name, transpose, quantize.

The musical `key` field lives at file byte 187 (not adjacent to the rest
of metadata — MidiSettings sits between name and key in the binary
format). For ergonomics it's still exposed as `project.metadata.key` but
M8Project handles the actual byte read/write at offset 187 separately
from M8Metadata's contiguous 146-byte block.

Earlier versions of pym8 treated file byte 160 as `key` — that was wrong
(it's `M8MidiSettings.receive_sync`). The byte happens to round-trip
either way; nothing in pym8 actually consumed `metadata.key`
semantically, so the rename is non-breaking for byte-output but does
move `metadata.key` to a different file byte.
"""
import struct

from m8.api import _read_fixed_string, _write_fixed_string


METADATA_OFFSET = 14
METADATA_BLOCK_SIZE = 146  # directory + transpose + tempo + quantize + name

# Field offsets within metadata block
DIRECTORY_OFFSET = 0
DIRECTORY_LENGTH = 128
TRANSPOSE_OFFSET = 128
TEMPO_OFFSET = 129
TEMPO_SIZE = 4
QUANTIZE_OFFSET = 133
NAME_OFFSET = 134
NAME_LENGTH = 12

# Defaults
DEFAULT_DIRECTORY = '/Songs/'
DEFAULT_TRANSPOSE = 0
DEFAULT_TEMPO = 120.0
DEFAULT_QUANTIZE = 0
DEFAULT_NAME = 'HELLO'
DEFAULT_KEY = 0


class M8Metadata:
    """Project metadata. `key` is stored here but written by M8Project at
    file byte 187 (after MidiSettings); the contiguous metadata block is
    just the first 146 bytes ending at the project name."""

    BLOCK_SIZE = METADATA_BLOCK_SIZE

    def __init__(self, directory=DEFAULT_DIRECTORY,
                 transpose=DEFAULT_TRANSPOSE,
                 tempo=DEFAULT_TEMPO,
                 quantize=DEFAULT_QUANTIZE,
                 name=DEFAULT_NAME,
                 key=DEFAULT_KEY):
        self.directory = directory
        self.transpose = transpose
        self.tempo = tempo
        self.quantize = quantize
        self.name = name
        self.key = key

    @classmethod
    def read(cls, data):
        """Parse the contiguous 146-byte metadata block. `key` is not in
        this block — M8Project sets it from byte 187 after calling read."""
        instance = cls()
        instance.directory = _read_fixed_string(data, DIRECTORY_OFFSET, DIRECTORY_LENGTH)
        instance.transpose = data[TRANSPOSE_OFFSET]
        instance.tempo = struct.unpack('<f', data[TEMPO_OFFSET:TEMPO_OFFSET + TEMPO_SIZE])[0]
        instance.quantize = data[QUANTIZE_OFFSET]
        instance.name = _read_fixed_string(data, NAME_OFFSET, NAME_LENGTH)
        # key is preserved across read() so callers that copy metadata
        # objects don't lose it; M8Project overwrites it after read.
        instance.key = DEFAULT_KEY
        return instance

    def write(self):
        """Serialize the 146-byte contiguous block. The `key` byte is
        written separately by M8Project at file offset 187."""
        buffer = bytearray()
        buffer.extend(_write_fixed_string(self.directory, DIRECTORY_LENGTH))
        buffer.append(self.transpose & 0xFF)
        buffer.extend(struct.pack('<f', self.tempo))
        buffer.append(self.quantize & 0xFF)
        buffer.extend(_write_fixed_string(self.name, NAME_LENGTH))
        assert len(buffer) == self.BLOCK_SIZE, (
            f"Buffer size mismatch: {len(buffer)} != {self.BLOCK_SIZE}"
        )
        return bytes(buffer)

    def clone(self):
        return M8Metadata(
            directory=self.directory,
            transpose=self.transpose,
            tempo=self.tempo,
            quantize=self.quantize,
            name=self.name,
            key=self.key,
        )
