# m8/api/instrument_file.py
"""M8 single-instrument files (.m8i).

Layout (m8-file-parser's `InstrumentWithEq`, instruments/mod.rs):

    0x000  "M8VERSION\\0"                10 bytes
    0x00A  version                       4 bytes
    0x00E  instrument                  215 bytes — same layout as an .m8s slot
    0x0E5  instrument table            128 bytes (16 steps × 8)
    0x165  EQ                           18 bytes — only when the instrument
                                                   has one (firmware 4.0+)

So a file is 357 bytes without an EQ and 375 with one.

Files from firmware before 3.0 store modulators untyped at instrument
offset 61 (slots fixed as AHD, AHD, LFO, LFO; LFO bytes reordered) instead
of typed at 63 — m8-file-parser's `from_reader2` vs `from_reader3` split
in instruments/common.rs. They're converted to the typed in-memory layout
on read, which makes them read-only: writing one back would put typed
modulators under a pre-3.0 version header.
"""

from m8.api.eq import M8Eq, EQ_BYTES, NO_EQ
from m8.api.instrument import BLOCK_SIZE, TYPE_OFFSET, _INSTRUMENT_REGISTRY
from m8.api.modulator import M8Modulators
from m8.api.table import M8Table, TABLE_BYTES
from m8.api.version import M8Version

MAGIC = b"M8VERSION\x00"
VERSION_OFFSET = 10
INSTRUMENT_OFFSET = 14
TABLE_OFFSET = INSTRUMENT_OFFSET + BLOCK_SIZE    # 0x0E5
EQ_OFFSET = TABLE_OFFSET + TABLE_BYTES           # 0x165
FILE_BYTES = EQ_OFFSET                           # 357, no EQ

V2_MODULATORS_OFFSET = 61
TYPED_MODULATORS_VERSION = (3, 0, 0)
EQ_VERSION = (4, 0, 0)


class M8InstrumentFile:
    """An instrument plus the table and optional EQ exported alongside it.

    `table` is the instrument's own table (table slot N for instrument N in
    a project). `eq` is the EQ the instrument's `associated_eq` pointed at
    when it was exported, or None. Neither is wired into a project here —
    the caller decides which project slots they land in.
    """

    def __init__(self, instrument, table=None, eq=None, version=None):
        self.instrument = instrument
        self.table = table if table is not None else M8Table()
        self.eq = eq
        self.version = version if version is not None else M8Version()

    @classmethod
    def read(cls, data):
        # Eagerly import every subclass so the registry is populated.
        from m8.api.instruments import sampler, wavsynth, macrosynth, fmsynth, external, midiout, hypersynth  # noqa: F401

        if len(data) < TABLE_OFFSET:
            raise ValueError(
                f"Data too short to be a M8 instrument file: {len(data)} bytes, "
                f"need at least {TABLE_OFFSET}"
            )

        version = M8Version.read(data[VERSION_OFFSET:])
        instrument_data = data[INSTRUMENT_OFFSET:TABLE_OFFSET]
        instr_type = instrument_data[TYPE_OFFSET]
        subclass = _INSTRUMENT_REGISTRY.get(instr_type)
        if subclass is None:
            raise ValueError(f"Unsupported instrument type 0x{instr_type:02X}")

        instrument = subclass.read(instrument_data, version=version)
        if version < TYPED_MODULATORS_VERSION:
            instrument.modulators = M8Modulators.read_v2(instrument_data[V2_MODULATORS_OFFSET:])
            # Byte 62 is modulator data in this layout, not an EQ index.
            instrument.associated_eq = NO_EQ

        # Firmware 1.x files are 349 bytes — too short for a full table.
        table = M8Table.read(data[TABLE_OFFSET:EQ_OFFSET]) if len(data) >= EQ_OFFSET else M8Table()

        eq = None
        if version >= EQ_VERSION and len(data) >= EQ_OFFSET + EQ_BYTES:
            eq = M8Eq.read(data[EQ_OFFSET:EQ_OFFSET + EQ_BYTES])

        return cls(instrument, table=table, eq=eq, version=version)

    @classmethod
    def read_from_file(cls, filename):
        with open(filename, "rb") as f:
            return cls.read(f.read())

    def write(self):
        if self.version < TYPED_MODULATORS_VERSION:
            raise ValueError(
                f"Can't write a firmware {self.version} instrument file: pym8 only "
                "writes the typed (3.0+) modulator layout"
            )
        output = bytearray(MAGIC + self.version.write())
        output += self.instrument.write()
        output += self.table.write()
        if self.eq is not None:
            output += self.eq.write()
        return bytes(output)

    def write_to_file(self, filename):
        import os

        directory = os.path.dirname(filename)
        if directory:
            os.makedirs(directory, exist_ok=True)
        with open(filename, "wb") as f:
            f.write(self.write())
