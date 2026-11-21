# m8/api/scale.py
"""M8 scales — microtonal tuning maps.

16 scales × 46 bytes at file offset 0x1AA7E (109182). Layout follows
m8-file-parser/src/scale.rs (which models the first 42 bytes; the
trailing 4 bytes are reserved/padding preserved verbatim).

Each scale's 46-byte block:

    bytes 0-1     enabled bitmap (u16 LE, low 12 bits flag the 12 notes
                  of an octave; bit i = note i enabled)
    bytes 2-25    12 × (int_semitone, cents) — per-note offsets. Both
                  bytes are raw u8; range is conceptually -24..24
                  semitones, but pym8 doesn't reinterpret signedness.
    bytes 26-41   name (16-byte 0xFF-padded string)
    bytes 42-45   reserved (round-trips as raw bytes)

The 12 notes index from C (note 0) to B (note 11).
"""
import struct

from m8.api import _read_fixed_string, _write_fixed_string
from m8.api.fields import M8FixedList, repr_value


SCALE_BYTES = 46
SCALE_COUNT = 16
SCALE_NOTE_COUNT = 12

BITMAP_OFFSET = 0
NOTES_OFFSET = 2
NOTE_PAIR_BYTES = 2
NAME_OFFSET = 26
NAME_LENGTH = 16
RESERVED_OFFSET = 42
RESERVED_LENGTH = 4

NOTE_NAMES = ("C", "CS", "D", "DS", "E", "F", "FS", "G", "GS", "A", "AS", "B")


class M8ScaleNote:
    """One note of a scale, as a live view into the scale's bytes.

    `enabled` is the note's bit in the scale's bitmap; `semitones` and
    `cents` are its two raw offset bytes (m8-file-parser reads the offset
    as semitones + cents / 100).
    """

    __slots__ = ("_scale", "index")

    def __init__(self, scale, index):
        self._scale = scale
        self.index = index

    @property
    def name(self):
        return NOTE_NAMES[self.index]

    @property
    def enabled(self):
        return bool(self._scale.enabled_bitmap & (1 << self.index))

    @enabled.setter
    def enabled(self, on):
        bitmap = self._scale.enabled_bitmap
        self._scale.enabled_bitmap = bitmap | (1 << self.index) if on else bitmap & ~(1 << self.index)

    def _byte(self, offset):
        return self._scale._data[NOTES_OFFSET + self.index * NOTE_PAIR_BYTES + offset]

    def _set_byte(self, offset, value, name):
        value = int(value)
        if not 0 <= value <= 0xFF:
            raise ValueError(f"{name}={value} out of range [0, 255]")
        self._scale._data[NOTES_OFFSET + self.index * NOTE_PAIR_BYTES + offset] = value

    @property
    def semitones(self):
        return self._byte(0)

    @semitones.setter
    def semitones(self, value):
        self._set_byte(0, value, "semitones")

    @property
    def cents(self):
        return self._byte(1)

    @cents.setter
    def cents(self, value):
        self._set_byte(1, value, "cents")

    def __repr__(self):
        return f"M8ScaleNote({self.name}, enabled={self.enabled}, semitones={self.semitones}, cents={self.cents})"


class M8Scale:
    """One microtonal scale: 12 notes, each with enabled flag + offset."""

    BYTES = SCALE_BYTES
    NOTE_COUNT = SCALE_NOTE_COUNT

    def __init__(self, name="", **kwargs):
        self._data = bytearray(self.BYTES)
        # Default: all 12 notes enabled, no offsets, empty name
        self._set_bitmap(0x0FFF)
        if name:
            self.name = name
        for key, value in kwargs.items():
            setattr(self, key, value)

    # --- enabled bitmap ---

    @property
    def enabled_bitmap(self):
        """Raw 16-bit bitmap (low 12 bits flag the 12 notes)."""
        return struct.unpack("<H", bytes(self._data[BITMAP_OFFSET:BITMAP_OFFSET + 2]))[0]

    @enabled_bitmap.setter
    def enabled_bitmap(self, value):
        self._set_bitmap(value)

    def _set_bitmap(self, value):
        self._data[BITMAP_OFFSET:BITMAP_OFFSET + 2] = struct.pack("<H", int(value) & 0xFFFF)

    @property
    def notes(self):
        """The 12 notes (C..B) as live views: `scale.notes[4].enabled = False`,
        `scale.notes[4].cents = 50`."""
        return tuple(M8ScaleNote(self, i) for i in range(self.NOTE_COUNT))

    # --- name ---

    @property
    def name(self):
        return _read_fixed_string(self._data, NAME_OFFSET, NAME_LENGTH)

    @name.setter
    def name(self, value):
        self._data[NAME_OFFSET:NAME_OFFSET + NAME_LENGTH] = _write_fixed_string(
            value or "", NAME_LENGTH,
        )

    # --- serialization ---

    def __repr__(self):
        """Enabled notes with their offsets, e.g. M8Scale('MAJOR', C=+0.00, D=+0.00, ...)."""
        notes = [f"{n.name}=+{n.semitones}.{n.cents:02d}" for n in self.notes if n.enabled]
        return f"M8Scale({self.name!r}, " + ", ".join(notes) + ")"

    @classmethod
    def read(cls, data):
        instance = cls.__new__(cls)
        instance._data = bytearray(data[:cls.BYTES])
        return instance

    def write(self):
        return bytes(self._data)

    def clone(self):
        instance = self.__class__.__new__(self.__class__)
        instance._data = bytearray(self._data)
        return instance

    def to_dict(self):
        return {
            "name": self.name,
            "enabled_bitmap": self.enabled_bitmap,
            "notes": [
                {"enabled": n.enabled, "semitones": n.semitones, "cents": n.cents}
                for n in self.notes
            ],
        }

    @classmethod
    def from_dict(cls, d):
        instance = cls()
        if "name" in d:
            instance.name = d["name"]
        if "enabled_bitmap" in d:
            instance.enabled_bitmap = d["enabled_bitmap"]
        for view, note in zip(instance.notes, d.get("notes", [])):
            for key in ("enabled", "semitones", "cents"):
                if key in note:
                    setattr(view, key, note[key])
        return instance


class M8Scales(M8FixedList):
    """16 scales at file offset 0x1AA7E (109182)."""

    COUNT = SCALE_COUNT
    TOTAL_BYTES = SCALE_COUNT * SCALE_BYTES

    def __repr__(self):
        return "M8Scales(" + ", ".join(repr(s.name) for s in self) + ")"

    def __init__(self):
        super().__init__()
        for _ in range(self.COUNT):
            list.append(self, M8Scale())

    @classmethod
    def read(cls, data, version=None):
        instance = cls.__new__(cls)
        list.__init__(instance)
        for i in range(cls.COUNT):
            start = i * SCALE_BYTES
            block = data[start:start + SCALE_BYTES]
            if len(block) < SCALE_BYTES:
                block = block + bytes(SCALE_BYTES - len(block))
            list.append(instance, M8Scale.read(block))
        return instance

    def write(self):
        return b"".join(s.write() for s in self)

    def clone(self):
        instance = self.__class__.__new__(self.__class__)
        list.__init__(instance)
        for s in self:
            list.append(instance, s.clone())
        return instance

    def to_dict(self):
        return [s.to_dict() for s in self]

    @classmethod
    def from_dict(cls, items):
        instance = cls.__new__(cls)
        list.__init__(instance)
        for item in items[:cls.COUNT]:
            list.append(instance, M8Scale.from_dict(item))
        while len(instance) < cls.COUNT:
            list.append(instance, M8Scale())
        return instance
