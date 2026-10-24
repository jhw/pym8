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

    def is_note_enabled(self, note):
        if not 0 <= note < self.NOTE_COUNT:
            raise IndexError(f"note {note} out of range [0, {self.NOTE_COUNT - 1}]")
        return bool(self.enabled_bitmap & (1 << note))

    def set_note_enabled(self, note, enabled):
        if not 0 <= note < self.NOTE_COUNT:
            raise IndexError(f"note {note} out of range [0, {self.NOTE_COUNT - 1}]")
        bitmap = self.enabled_bitmap
        if enabled:
            bitmap |= 1 << note
        else:
            bitmap &= ~(1 << note)
        self._set_bitmap(bitmap)

    # --- per-note (int_semitone, cents) offsets ---

    def get_note_offset(self, note):
        """Return (int_semitones, cents) as raw bytes for note 0..11."""
        if not 0 <= note < self.NOTE_COUNT:
            raise IndexError(f"note {note} out of range [0, {self.NOTE_COUNT - 1}]")
        base = NOTES_OFFSET + note * NOTE_PAIR_BYTES
        return (self._data[base], self._data[base + 1])

    def set_note_offset(self, note, semitones, cents):
        if not 0 <= note < self.NOTE_COUNT:
            raise IndexError(f"note {note} out of range [0, {self.NOTE_COUNT - 1}]")
        base = NOTES_OFFSET + note * NOTE_PAIR_BYTES
        self._data[base] = int(semitones) & 0xFF
        self._data[base + 1] = int(cents) & 0xFF

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
                {
                    "enabled": self.is_note_enabled(i),
                    "semitones": self.get_note_offset(i)[0],
                    "cents": self.get_note_offset(i)[1],
                }
                for i in range(self.NOTE_COUNT)
            ],
        }

    @classmethod
    def from_dict(cls, d):
        instance = cls()
        if "name" in d:
            instance.name = d["name"]
        if "enabled_bitmap" in d:
            instance.enabled_bitmap = d["enabled_bitmap"]
        for i, note in enumerate(d.get("notes", [])[:cls.NOTE_COUNT]):
            if "enabled" in note:
                instance.set_note_enabled(i, note["enabled"])
            if "semitones" in note or "cents" in note:
                instance.set_note_offset(
                    i,
                    note.get("semitones", 0),
                    note.get("cents", 0),
                )
        return instance


class M8Scales(list):
    """16 scales at file offset 0x1AA7E (109182)."""

    COUNT = SCALE_COUNT
    TOTAL_BYTES = SCALE_COUNT * SCALE_BYTES

    def __init__(self):
        super().__init__()
        for _ in range(self.COUNT):
            self.append(M8Scale())

    @classmethod
    def read(cls, data, version=None):
        instance = cls.__new__(cls)
        list.__init__(instance)
        for i in range(cls.COUNT):
            start = i * SCALE_BYTES
            block = data[start:start + SCALE_BYTES]
            if len(block) < SCALE_BYTES:
                block = block + bytes(SCALE_BYTES - len(block))
            instance.append(M8Scale.read(block))
        return instance

    def write(self):
        return b"".join(s.write() for s in self)

    def clone(self):
        instance = self.__class__.__new__(self.__class__)
        list.__init__(instance)
        for s in self:
            instance.append(s.clone())
        return instance

    def to_dict(self):
        return [s.to_dict() for s in self]

    @classmethod
    def from_dict(cls, items):
        instance = cls.__new__(cls)
        list.__init__(instance)
        for item in items[:cls.COUNT]:
            instance.append(M8Scale.from_dict(item))
        while len(instance) < cls.COUNT:
            instance.append(M8Scale())
        return instance
