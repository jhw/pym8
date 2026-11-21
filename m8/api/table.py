# m8/api/table.py
"""M8 tables — 256 × 16-step modulation tables.

Layout follows m8-file-parser/src/songs.rs (Table / TableStep).

Each `M8TableStep` is 8 bytes:
  byte 0  transpose
  byte 1  velocity   (0xFF = empty / "no override")
  byte 2  fx1.key
  byte 3  fx1.value
  byte 4  fx2.key
  byte 5  fx2.value
  byte 6  fx3.key
  byte 7  fx3.value

Each `M8Table` is 16 steps = 128 bytes.
The collection of 256 tables is 32 768 bytes at file offset 0xBA3E (47678).

Tables are reference-bearing: each step's FX commands can target an
instrument (via I-class FX codes), another table (via T-class), or an
EQ (via EQ-class). When the remapper lands, it'll need to walk every
step's three FX slots and rewrite those reference values.
"""

from m8.api.fields import ByteField, M8Record, iter_fields, repr_slots, repr_steps
from m8.api.fx import M8FXTuples


TABLE_OFFSET = 47678              # 0xBA3E
TABLE_COUNT = 256
TABLE_STEP_COUNT = 16
TABLE_STEP_BYTES = 8              # transpose + velocity + 3 × (key,value)
TABLE_BYTES = TABLE_STEP_COUNT * TABLE_STEP_BYTES   # 128
TABLES_TOTAL_BYTES = TABLE_COUNT * TABLE_BYTES      # 32768

EMPTY_VELOCITY = 0xFF
DEFAULT_TRANSPOSE = 0


class M8TableStep(M8Record):
    """One step in a table: transpose + velocity + 3 FX slots.

    `fx` is a separate M8FXTuples attribute merged into the byte buffer at
    write time, as on M8PhraseStep.
    """

    BYTES = TABLE_STEP_BYTES
    BASE_BYTES = 2

    transpose = ByteField(0, default=DEFAULT_TRANSPOSE)
    velocity  = ByteField(1, default=EMPTY_VELOCITY)

    def __init__(self, **kwargs):
        self._data = bytearray(self.BASE_BYTES)
        for _, fld in iter_fields(type(self)):
            fld.apply_default(self)
        self.fx = M8FXTuples()
        for key, value in kwargs.items():
            setattr(self, key, value)

    def is_empty(self):
        """Match Rust's `is_empty`: default transpose, default velocity, no FX."""
        return (
            self.transpose == DEFAULT_TRANSPOSE
            and self.velocity == EMPTY_VELOCITY
            and all(tup.key == 0xFF for tup in self.fx)
        )

    @classmethod
    def read(cls, data):
        instance = cls.__new__(cls)
        instance._data = bytearray(data[:cls.BASE_BYTES])
        instance.fx = M8FXTuples.read(data[cls.BASE_BYTES:cls.BYTES])
        return instance

    def write(self):
        return bytes(self._data) + self.fx.write()

    def clone(self):
        instance = self.__class__.__new__(self.__class__)
        instance._data = bytearray(self._data)
        instance.fx = self.fx.clone()
        return instance

    def to_dict(self):
        d = super().to_dict()
        d["fx"] = self.fx.to_dict()
        return d

    @classmethod
    def from_dict(cls, d):
        instance = super().from_dict(d)
        if "fx" in d:
            instance.fx = M8FXTuples.from_dict(d["fx"])
        return instance

    def _repr_fields(self):
        fields = super()._repr_fields()
        return fields + [("fx", self.fx)] if not self.fx.is_empty() else fields


class M8Table(list):
    """16 table steps — list-like of M8TableStep."""

    COUNT = TABLE_STEP_COUNT
    BYTES = TABLE_BYTES

    def __init__(self):
        super().__init__()
        for _ in range(self.COUNT):
            self.append(M8TableStep())

    def __repr__(self):
        return repr_steps(self)

    @classmethod
    def read(cls, data):
        instance = cls.__new__(cls)
        list.__init__(instance)
        for i in range(cls.COUNT):
            start = i * TABLE_STEP_BYTES
            instance.append(M8TableStep.read(data[start:start + TABLE_STEP_BYTES]))
        return instance

    def write(self):
        return b"".join(step.write() for step in self)

    def clone(self):
        instance = self.__class__.__new__(self.__class__)
        list.__init__(instance)
        for step in self:
            instance.append(step.clone())
        return instance

    def is_empty(self):
        return all(step.is_empty() for step in self)

    def to_dict(self):
        return [step.to_dict() for step in self]

    @classmethod
    def from_dict(cls, items):
        instance = cls.__new__(cls)
        list.__init__(instance)
        for item in items[:cls.COUNT]:
            instance.append(M8TableStep.from_dict(item))
        while len(instance) < cls.COUNT:
            instance.append(M8TableStep())
        return instance


class M8Tables(list):
    """256 tables at file offset 0xBA3E."""

    COUNT = TABLE_COUNT
    TOTAL_BYTES = TABLES_TOTAL_BYTES

    def __init__(self):
        super().__init__()
        for _ in range(self.COUNT):
            self.append(M8Table())

    def __repr__(self):
        return repr_slots(self, (i for i, t in enumerate(self) if not t.is_empty()))

    @classmethod
    def read(cls, data, version=None):
        """`version` accepted for forward compat (no firmware-conditional
        layout in the byte format — Rust threads it for FX-command name
        resolution, not for the binary read)."""
        instance = cls.__new__(cls)
        list.__init__(instance)
        for i in range(cls.COUNT):
            start = i * TABLE_BYTES
            instance.append(M8Table.read(data[start:start + TABLE_BYTES]))
        return instance

    def write(self):
        return b"".join(table.write() for table in self)

    def clone(self):
        instance = self.__class__.__new__(self.__class__)
        list.__init__(instance)
        for table in self:
            instance.append(table.clone())
        return instance

    def to_dict(self):
        return [table.to_dict() for table in self]

    @classmethod
    def from_dict(cls, items):
        instance = cls.__new__(cls)
        list.__init__(instance)
        for item in items[:cls.COUNT]:
            instance.append(M8Table.from_dict(item))
        while len(instance) < cls.COUNT:
            instance.append(M8Table())
        return instance
