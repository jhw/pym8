# m8/api/fields.py
"""Typed-field descriptors over a backing bytearray.

Descriptors are the canonical declaration of an instrument's parameters:
where they live in the binary block, what enum (if any) they belong to,
their default at construction, and how they serialize to/from dicts.

The backing `_data` bytearray remains the source of truth on disk — descriptors
are a typed view over it. Bytes not covered by a descriptor round-trip
unchanged, which is what makes the format-faithful read/write work even when
pym8 doesn't yet model every byte.
"""

from m8.api import _read_fixed_string, _write_fixed_string


class ByteField:
    """Single unsigned byte at a fixed offset."""

    __slots__ = ("offset", "default", "enum", "min", "max", "name")

    def __init__(self, offset, default=0, enum=None, min=0, max=255):
        self.offset = offset
        self.default = default
        self.enum = enum
        self.min = min
        self.max = max
        self.name = None

    def __set_name__(self, owner, name):
        self.name = name

    def __get__(self, obj, objtype=None):
        if obj is None:
            return self
        return obj._data[self.offset]

    def __set__(self, obj, value):
        if hasattr(value, "value"):
            value = value.value
        value = int(value)
        if not self.min <= value <= self.max:
            raise ValueError(
                f"{self.name}={value} out of range [{self.min}, {self.max}]"
            )
        obj._data[self.offset] = value

    def apply_default(self, obj):
        obj._data[self.offset] = self.default & 0xFF

    def to_dict(self, obj):
        value = obj._data[self.offset]
        if self.enum is not None:
            try:
                return self.enum(value).name
            except ValueError:
                pass
        return value

    def from_dict(self, obj, value):
        if isinstance(value, str) and self.enum is not None:
            value = self.enum[value].value
        self.__set__(obj, value)


class StringField:
    """Fixed-length null-padded UTF-8 string."""

    __slots__ = ("offset", "length", "default", "name")

    def __init__(self, offset, length, default=""):
        self.offset = offset
        self.length = length
        self.default = default
        self.name = None

    def __set_name__(self, owner, name):
        self.name = name

    def __get__(self, obj, objtype=None):
        if obj is None:
            return self
        return _read_fixed_string(obj._data, self.offset, self.length)

    def __set__(self, obj, value):
        encoded = _write_fixed_string(value or "", self.length)
        obj._data[self.offset:self.offset + self.length] = encoded

    def apply_default(self, obj):
        if self.default:
            self.__set__(obj, self.default)

    def to_dict(self, obj):
        return self.__get__(obj)

    def from_dict(self, obj, value):
        self.__set__(obj, value)


class BytesField:
    """Fixed-length raw byte sequence — exposed as a list[int] of ints in [0, 255].

    Used for short, semantically opaque byte arrays like HyperSynth's
    default_chord (7 bytes of semitone offsets). For structured records,
    prefer a separate sub-object stored as a regular Python attribute (see
    M8Modulators / M8HyperSynthChords) — descriptors stop being a clean fit
    once each element has internal structure.
    """

    __slots__ = ("offset", "length", "default", "name")

    def __init__(self, offset, length, default=None):
        self.offset = offset
        self.length = length
        self.default = list(default) if default is not None else [0] * length
        if len(self.default) != length:
            raise ValueError(f"BytesField default must be {length} bytes")
        self.name = None

    def __set_name__(self, owner, name):
        self.name = name

    def __get__(self, obj, objtype=None):
        if obj is None:
            return self
        return list(obj._data[self.offset:self.offset + self.length])

    def __set__(self, obj, value):
        value = list(value)
        if len(value) != self.length:
            raise ValueError(f"{self.name} must be {self.length} bytes, got {len(value)}")
        obj._data[self.offset:self.offset + self.length] = bytes(int(b) & 0xFF for b in value)

    def apply_default(self, obj):
        obj._data[self.offset:self.offset + self.length] = bytes(self.default)

    def to_dict(self, obj):
        return self.__get__(obj)

    def from_dict(self, obj, value):
        self.__set__(obj, value)


_FIELD_TYPES = (ByteField, StringField, BytesField)


def iter_fields(cls):
    """Yield (name, descriptor) for every field descriptor on cls and its bases.

    Subclass declarations win when a name is declared in both subclass and base.
    Resolution order: subclass fields first (in declaration order), then each
    successive base, skipping names already collected.
    """
    seen = set()
    subclass_order = []
    inherited_order = []
    for index, klass in enumerate(cls.__mro__):
        for name, attr in vars(klass).items():
            if isinstance(attr, _FIELD_TYPES) and name not in seen:
                seen.add(name)
                target = subclass_order if index == 0 else inherited_order
                target.append((name, attr))
    return subclass_order + inherited_order
