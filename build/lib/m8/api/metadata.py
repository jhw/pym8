# m8/api/metadata.py
"""M8 project metadata — directory, tempo, name, transpose, quantize.

This is the contiguous 146-byte block at file offset 14, ending at the
project name. The musical `key` byte is NOT here (it lives at file byte
187, after MidiSettings); it's a top-level attribute on M8Project
(`project.key`).
"""
import struct

from m8.api.fields import ByteField, StringField


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

    Backed by a raw 146-byte buffer (`_data`), same pattern as instruments
    (m8/api/instrument.py) and scales (m8/api/scale.py): fields read/write
    directly into the buffer in place, so bytes belonging to untouched
    fields — including stale data trailing a string's null terminator —
    round-trip byte-for-byte through read()/write() unless the field is
    actually reassigned.

    The musical `key` byte is on M8Project (`project.key`), not here —
    it lives at file byte 187 (after MidiSettings) so it isn't part of
    the contiguous metadata block.
    """

    BLOCK_SIZE = METADATA_BLOCK_SIZE

    directory = StringField(DIRECTORY_OFFSET, DIRECTORY_LENGTH, default=DEFAULT_DIRECTORY)
    transpose = ByteField(TRANSPOSE_OFFSET, default=DEFAULT_TRANSPOSE)
    quantize = ByteField(QUANTIZE_OFFSET, default=DEFAULT_QUANTIZE)
    name = StringField(NAME_OFFSET, NAME_LENGTH, default=DEFAULT_NAME)

    def __init__(self, directory=DEFAULT_DIRECTORY,
                 transpose=DEFAULT_TRANSPOSE,
                 tempo=DEFAULT_TEMPO,
                 quantize=DEFAULT_QUANTIZE,
                 name=DEFAULT_NAME):
        self._data = bytearray(self.BLOCK_SIZE)
        self.directory = directory
        self.transpose = transpose
        self.tempo = tempo
        self.quantize = quantize
        self.name = name

    @property
    def tempo(self):
        return struct.unpack('<f', bytes(self._data[TEMPO_OFFSET:TEMPO_OFFSET + TEMPO_SIZE]))[0]

    @tempo.setter
    def tempo(self, value):
        self._data[TEMPO_OFFSET:TEMPO_OFFSET + TEMPO_SIZE] = struct.pack('<f', float(value))

    @classmethod
    def read(cls, data):
        instance = cls.__new__(cls)
        instance._data = bytearray(data[:cls.BLOCK_SIZE])
        return instance

    def write(self):
        return bytes(self._data)

    def clone(self):
        instance = self.__class__.__new__(self.__class__)
        instance._data = bytearray(self._data)
        return instance
