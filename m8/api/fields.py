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

from enum import IntEnum

from m8.api import _read_fixed_string, _write_fixed_string


class ByteField:
    """Single unsigned byte at a fixed offset.

    With `enum=`, reads return the enum member when the byte is one of its
    values (an IntEnum, so it still compares and computes as an int) and
    the plain int otherwise.
    """

    __slots__ = ("offset", "default", "enum", "min", "max", "name", "_members")

    def __init__(self, offset, default=0, enum=None, min=0, max=255):
        self.offset = offset
        self.default = default
        self.enum = enum
        self.min = min
        self.max = max
        self.name = None
        self._members = {int(m): m for m in enum} if enum is not None else None

    def __set_name__(self, owner, name):
        self.name = name

    def __get__(self, obj, objtype=None):
        if obj is None:
            return self
        value = obj._data[self.offset]
        if self._members is not None:
            return self._members.get(value, value)
        return value

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


def enum_or_int(enum, value):
    """The enum member for `value`, or `value` itself if it isn't one."""
    try:
        return enum(value)
    except ValueError:
        return value


def repr_value(value):
    """Format a field value for __repr__: enum members by name, bytes in
    hex (as the M8 screen shows them), strings quoted, sequences
    element-wise."""
    if isinstance(value, IntEnum):
        return value.name
    if isinstance(value, bool):
        return repr(value)
    if isinstance(value, int):
        return f"0x{value:02X}"
    if isinstance(value, str):
        return repr(value)
    if type(value) in (list, tuple, _IndexedByteView):   # not subclasses with their own repr
        return "[" + ", ".join(repr_value(v) for v in value) + "]"
    return repr(value)


def index_ranges(indices):
    """[0, 1, 2, 5, 7, 8] -> '0-2, 5, 7-8'."""
    out, start, prev = [], None, None
    for i in indices:
        if start is None:
            start = prev = i
        elif i == prev + 1:
            prev = i
        else:
            out.append(f"{start}-{prev}" if prev > start else f"{start}")
            start = prev = i
    if start is not None:
        out.append(f"{start}-{prev}" if prev > start else f"{start}")
    return ", ".join(out)


def repr_steps(steps):
    """Repr for a fixed run of steps (phrase, chain, table): only the
    non-empty steps, keyed by step index."""
    filled = [(i, s) for i, s in enumerate(steps) if not s.is_empty()]
    if not filled:
        return f"{type(steps).__name__}(empty)"
    inner = ", ".join(f"{i}: {s!r}" for i, s in filled)
    return f"{type(steps).__name__}({{{inner}}})"


def repr_slots(collection, used):
    """Repr for a big slot collection (phrases, chains, ...): which slots
    are in use, not their contents — index into it to see one."""
    used = list(used)
    if not used:
        return f"{type(collection).__name__}(none used of {len(collection)})"
    return f"{type(collection).__name__}({len(used)} used of {len(collection)}: {index_ranges(used)})"


class M8FixedList(list):
    """A list with a fixed number of slots.

    Index, slice, iterate and assign as usual — but nothing may change the
    length or the order. Deleting slot 5 of a list would silently renumber
    slots 6+, and every phrase/chain/song reference to them would then
    point at the wrong thing while the file still wrote cleanly.

    Construction code inside pym8 fills instances with `list.append(x, ...)`
    directly, bypassing the guard.
    """

    #: What to do instead; subclasses tailor it.
    CLEAR_HINT = "assign a new, empty item to a slot to clear it"

    def _refuse(self, *args, **kwargs):
        raise TypeError(
            f"{type(self).__name__} has a fixed {len(self)} slots and can't grow, "
            f"shrink or be reordered; {self.CLEAR_HINT}"
        )

    append = extend = insert = pop = remove = clear = sort = reverse = _refuse
    __delitem__ = __iadd__ = __imul__ = _refuse

    def __setitem__(self, index, value):
        if isinstance(index, slice):
            value = list(value)
            if len(value) != len(range(*index.indices(len(self)))):
                self._refuse()
        list.__setitem__(self, index, value)


class M8Record:
    """Generic to_dict / from_dict / __repr__ for a descriptor-backed record.

    Every field declared on the class (and its bases) is included. Classes
    with structure beyond their descriptors (sub-records, properties)
    extend these rather than replacing them.
    """

    def to_dict(self):
        return {name: fld.to_dict(self) for name, fld in iter_fields(type(self))}

    @classmethod
    def from_dict(cls, d):
        """Build from a to_dict() dict. Unknown keys are ignored."""
        instance = cls()
        fields_by_name = dict(iter_fields(cls))
        for key, value in d.items():
            fld = fields_by_name.get(key)
            if fld is not None:
                fld.from_dict(instance, value)
        return instance

    def _repr_fields(self):
        return [(name, getattr(self, name)) for name, _ in iter_fields(type(self))]

    def __repr__(self):
        parts = ", ".join(f"{n}={repr_value(v)}" for n, v in self._repr_fields())
        return f"{type(self).__name__}({parts})"


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
