# m8/api/metadata.py
"""M8 project metadata — directory, tempo, name, transpose, quantize.

This is the contiguous 146-byte block at file offset 14, ending at the
project name. The musical `key` byte is NOT here (it lives at file byte
187, after MidiSettings); it's a top-level attribute on M8Project
(`project.key`).
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


class M8Metadata:
    """Project metadata: directory, transpose, tempo, quantize, name.

    The musical `key` byte is on M8Project (`project.key`), not here —
    it lives at file byte 187 (after MidiSettings) so it isn't part of
    the contiguous metadata block.
    """

    BLOCK_SIZE = METADATA_BLOCK_SIZE

    def __init__(self, directory=DEFAULT_DIRECTORY,
                 transpose=DEFAULT_TRANSPOSE,
                 tempo=DEFAULT_TEMPO,
                 quantize=DEFAULT_QUANTIZE,
                 name=DEFAULT_NAME):
        self.directory = directory
        self.transpose = transpose
        self.tempo = tempo
        self.quantize = quantize
        self.name = name

    @classmethod
    def read(cls, data):
        instance = cls()
        instance.directory = _read_fixed_string(data, DIRECTORY_OFFSET, DIRECTORY_LENGTH)
        instance.transpose = data[TRANSPOSE_OFFSET]
        instance.tempo = struct.unpack('<f', data[TEMPO_OFFSET:TEMPO_OFFSET + TEMPO_SIZE])[0]
        instance.quantize = data[QUANTIZE_OFFSET]
        instance.name = _read_fixed_string(data, NAME_OFFSET, NAME_LENGTH)
        return instance

    def write(self):
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
        )
