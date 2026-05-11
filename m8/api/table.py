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

from m8.api.fx import M8FXTuples


TABLE_OFFSET = 47678              # 0xBA3E
TABLE_COUNT = 256
TABLE_STEP_COUNT = 16
TABLE_STEP_BYTES = 8              # transpose + velocity + 3 × (key,value)
TABLE_BYTES = TABLE_STEP_COUNT * TABLE_STEP_BYTES   # 128
TABLES_TOTAL_BYTES = TABLE_COUNT * TABLE_BYTES      # 32768

EMPTY_VELOCITY = 0xFF
DEFAULT_TRANSPOSE = 0


class M8TableStep:
    """One step in a table: transpose + velocity + 3 FX slots."""

    BYTES = TABLE_STEP_BYTES

    def __init__(self, transpose=DEFAULT_TRANSPOSE, velocity=EMPTY_VELOCITY):
        self._data = bytearray([transpose & 0xFF, velocity & 0xFF])
        self.fx = M8FXTuples()

    @property
    def transpose(self):
        return self._data[0]

    @transpose.setter
    def transpose(self, value):
        if hasattr(value, "value"):
            value = value.value
        self._data[0] = int(value) & 0xFF

    @property
    def velocity(self):
        return self._data[1]

    @velocity.setter
    def velocity(self, value):
        if hasattr(value, "value"):
            value = value.value
        self._data[1] = int(value) & 0xFF

    def is_empty(self):
        """Match Rust's `is_empty`: default transpose, default velocity, no FX."""
        return (
            self.transpose == DEFAULT_TRANSPOSE
            and self.velocity == EMPTY_VELOCITY
            and all(tup.key == 0xFF for tup in self.fx)
        )

    @classmethod
    def read(cls, data):
        instance = cls()
        instance._data = bytearray(data[:2])
        instance.fx = M8FXTuples.read(data[2:cls.BYTES])
        return instance

    def write(self):
        return bytes(self._data) + self.fx.write()

    def clone(self):
        instance = self.__class__.__new__(self.__class__)
        instance._data = bytearray(self._data)
        instance.fx = self.fx.clone()
        return instance

    def to_dict(self):
        return {
            "transpose": self.transpose,
            "velocity": self.velocity,
            "fx": [{"key": tup.key, "value": tup.value} for tup in self.fx],
        }

    @classmethod
    def from_dict(cls, d):
        instance = cls(
            transpose=d.get("transpose", DEFAULT_TRANSPOSE),
            velocity=d.get("velocity", EMPTY_VELOCITY),
        )
        for i, fx_d in enumerate(d.get("fx", [])[:len(instance.fx)]):
            instance.fx[i].key = fx_d.get("key", 0xFF)
            instance.fx[i].value = fx_d.get("value", 0)
        return instance


class M8Table(list):
    """16 table steps — list-like of M8TableStep."""

    COUNT = TABLE_STEP_COUNT
    BYTES = TABLE_BYTES

    def __init__(self):
        super().__init__()
        for _ in range(self.COUNT):
            self.append(M8TableStep())

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
