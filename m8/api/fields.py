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


class _IndexedByteView:
    """Mutable list-like view into a fixed range of the parent object's _data.

    Returned by IndexedBytesField.__get__. Mutations propagate to the
    underlying bytearray.
    """

    __slots__ = ("_obj", "_offset", "_length")

    def __init__(self, obj, offset, length):
        self._obj = obj
        self._offset = offset
        self._length = length

    def _normalise(self, i):
        if i < 0:
            i += self._length
        if not 0 <= i < self._length:
            raise IndexError(f"index {i} out of range [0, {self._length - 1}]")
        return i

    def __len__(self):
        return self._length

    def __getitem__(self, i):
        return self._obj._data[self._offset + self._normalise(i)]

    def __setitem__(self, i, value):
        i = self._normalise(i)
        if hasattr(value, "value"):
            value = value.value
        self._obj._data[self._offset + i] = int(value) & 0xFF

    def __iter__(self):
        for i in range(self._length):
            yield self._obj._data[self._offset + i]

    def __eq__(self, other):
        return list(self) == list(other)

    def __ne__(self, other):
        return not self.__eq__(other)

    def __repr__(self):
        return f"[{', '.join(hex(b) for b in self)}]"


class IndexedBytesField:
    """Fixed-length byte array exposed as a mutable list-like view.

    Unlike `BytesField` (which returns a list copy and requires reassigning
    the whole slice to mutate), `IndexedBytesField` returns a live view —
    `obj.array[3] = 0x80` writes directly into `_data`. Use this for arrays
    where users naturally think "the N-th element" (e.g. per-track volumes,
    per-track input channels).
    """

    __slots__ = ("offset", "length", "default", "name")

    def __init__(self, offset, length, default=None):
        self.offset = offset
        self.length = length
        self.default = list(default) if default is not None else [0] * length
        if len(self.default) != length:
            raise ValueError(f"IndexedBytesField default must be {length} bytes")
        self.name = None

    def __set_name__(self, owner, name):
        self.name = name

    def __get__(self, obj, objtype=None):
        if obj is None:
            return self
        return _IndexedByteView(obj, self.offset, self.length)

    def __set__(self, obj, value):
        """Replace the whole array (assignment of a list of length `length`)."""
        value = list(value)
        if len(value) != self.length:
            raise ValueError(f"{self.name} must be {self.length} bytes, got {len(value)}")
        obj._data[self.offset:self.offset + self.length] = bytes(int(b) & 0xFF for b in value)

    def apply_default(self, obj):
        obj._data[self.offset:self.offset + self.length] = bytes(self.default)

    def to_dict(self, obj):
        return list(self.__get__(obj))

    def from_dict(self, obj, value):
        self.__set__(obj, value)


_FIELD_TYPES = (ByteField, StringField, BytesField, IndexedBytesField)


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
