# m8/api/instrument.py
"""M8 instrument base class and collection.

Each concrete instrument subclass declares its parameters as ByteField /
StringField descriptors. The base class handles construction, defaults,
binary read/write, cloning, and dict (de)serialization generically by walking
the descriptor set.
"""

import warnings
from enum import IntEnum

from m8.api import M8Block
from m8.api.eq import NO_EQ
from m8.api.fields import ByteField, M8FixedList, StringField, iter_fields, repr_value
from m8.api.modulator import M8Modulators
from m8.api.version import M8Version


INSTRUMENTS_OFFSET = 80446
INSTRUMENTS_BLOCK_SIZE = 215
INSTRUMENTS_COUNT = 128

# Offsets shared by every M8s instrument block.
TYPE_OFFSET = 0
NAME_OFFSET = 1
NAME_LENGTH = 12
MODULATORS_OFFSET = 63

BLOCK_SIZE = INSTRUMENTS_BLOCK_SIZE
BLOCK_COUNT = INSTRUMENTS_COUNT


class M8InstrumentType(IntEnum):
    WAVSYNTH = 0
    MACROSYNTH = 1
    SAMPLER = 2
    MIDIOUT = 3
    FMSYNTH = 4
    HYPERSYNTH = 5
    EXTERNAL = 6


class M8FilterType(IntEnum):
    """Filter type values shared across synth instruments."""
    OFF = 0x00
    LOWPASS = 0x01
    HIGHPASS = 0x02
    BANDPASS = 0x03
    BANDSTOP = 0x04
    LP_HP = 0x05
    ZDF_LP = 0x06
    ZDF_HP = 0x07


class M8LimiterType(IntEnum):
    """Limiter / clipping algorithm values."""
    CLIP = 0x00
    SIN = 0x01
    FOLD = 0x02
    WRAP = 0x03
    POST = 0x04
    POSTAD = 0x05
    POST_W1 = 0x06
    POST_W2 = 0x07
    POST_W3 = 0x08


_INSTRUMENT_REGISTRY = {}


class M8Instrument:
    """Base class for all M8 instrument types.

    Subclasses must set TYPE_ID and declare their parameter descriptors.
    The base class supplies `name` and `modulators` and handles read/write,
    clone, and dict (de)serialization generically.
    """

    TYPE_ID = None
    MOD_DEST_ENUM_CLASS = None

    name = StringField(NAME_OFFSET, NAME_LENGTH)
    # associated_eq lives at the byte just before modulators (firmware 5.0+).
    # Indexes the instrument EQs (0-127); >= 128 means "no EQ assigned",
    # and the firmware writes NO_EQ (0x80) for that.
    associated_eq = ByteField(MODULATORS_OFFSET - 1, default=NO_EQ)

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if cls.TYPE_ID is not None:
            _INSTRUMENT_REGISTRY[int(cls.TYPE_ID)] = cls

    def __init__(self, **kwargs):
        if self.TYPE_ID is None:
            raise TypeError(f"{type(self).__name__} must declare TYPE_ID")
        self._data = bytearray(BLOCK_SIZE)
        self._data[TYPE_OFFSET] = int(self.TYPE_ID)
        self.version = M8Version()
        self.modulators = M8Modulators()
        for _, fld in iter_fields(type(self)):
            fld.apply_default(self)
        for key, value in kwargs.items():
            if value is None or value == "":
                continue
            setattr(self, key, value)

    @property
    def type_id(self):
        return self._data[TYPE_OFFSET]

    def write(self):
        buffer = bytearray(self._data)
        mod_data = self.modulators.write()
        buffer[MODULATORS_OFFSET:MODULATORS_OFFSET + len(mod_data)] = mod_data
        return bytes(buffer)

    def clone(self):
        instance = self.__class__.__new__(self.__class__)
        instance._data = bytearray(self._data)
        instance.version = self.version.clone()
        instance.modulators = self.modulators.clone()
        return instance

    @classmethod
    def read(cls, data, version=None):
        """Parse a single instrument block from binary.

        `version` is the project's firmware version; subclasses with
        version-conditional layout (EQ packing in v6.0+, SynthParams in
        v3.0+, etc.) should consult it. Defaults to the bundled template
        firmware when not provided.
        """
        instance = cls.__new__(cls)
        instance._data = bytearray(data[:BLOCK_SIZE])
        instance.version = version if version is not None else M8Version()
        instance.modulators = M8Modulators.read(data[MODULATORS_OFFSET:])
        return instance

    def __repr__(self):
        """Every parameter, then the modulators with destinations named.
        Long for big instruments — it's meant to show everything."""
        parts = [repr(self.name)]
        parts += [f"{n}={repr_value(getattr(self, n))}" for n, _ in iter_fields(type(self)) if n != "name"]
        mods = ", ".join(m.repr_with(self.MOD_DEST_ENUM_CLASS) for m in self.modulators)
        parts.append(f"modulators=[{mods}]")
        return f"{type(self).__name__}({', '.join(parts)})"

    def to_dict(self):
        """Serialize to a name-keyed dict suitable for YAML/JSON.

        All enums are serialized by name; ints stay ints. Reverse of from_dict().
        """
        try:
            type_name = M8InstrumentType(self.type_id).name
        except ValueError:
            type_name = self.type_id

        params = {}
        for name, fld in iter_fields(type(self)):
            if name == "name":
                continue
            params[name] = fld.to_dict(self)

        return {
            "type": type_name,
            "name": self.name,
            "params": params,
            "modulators": self.modulators.to_dict(dest_enum_class=self.MOD_DEST_ENUM_CLASS),
        }

    @classmethod
    def from_dict(cls, params):
        """Reconstruct from a dict produced by to_dict().

        When called on M8Instrument (the base), dispatches to the appropriate
        subclass based on the `type` field. Accepts both enum names and int
        values for enum-typed parameters.
        """
        if cls is M8Instrument and "type" in params:
            # Eagerly import subclasses so the registry is populated.
            from m8.api.instruments import sampler, wavsynth, macrosynth, fmsynth, external, midiout, hypersynth  # noqa: F401

            type_value = params["type"]
            if isinstance(type_value, str):
                try:
                    type_id = int(M8InstrumentType[type_value])
                except KeyError:
                    raise ValueError(f"Unknown instrument type name: {type_value}")
            else:
                type_id = int(type_value)
            subclass = _INSTRUMENT_REGISTRY.get(type_id)
            if subclass is None:
                raise ValueError(f"No subclass registered for instrument type 0x{type_id:02X}")
            return subclass.from_dict(params)

        instance = cls()
        if "name" in params:
            instance.name = params["name"]

        fields_by_name = {name: fld for name, fld in iter_fields(cls)}
        for key, value in params.get("params", {}).items():
            fld = fields_by_name.get(key)
            if fld is None:
                continue  # forward-compatible: ignore unknown keys
            fld.from_dict(instance, value)

        if "modulators" in params:
            instance.modulators = M8Modulators.from_dict(
                params["modulators"], dest_enum_class=cls.MOD_DEST_ENUM_CLASS
            )
        return instance


def _label(instrument):
    """The instrument's name, or for an unnamed sampler its sample's file name."""
    if instrument.name:
        return instrument.name
    path = getattr(instrument, "sample_path", "")
    return path.rsplit("/", 1)[-1] if path else ""


class M8Instruments(M8FixedList):
    """The 128-slot instrument collection inside a project."""

    CLEAR_HINT = "use clear_slot(i) to empty a slot"

    @staticmethod
    def empty_block():
        """The canonical empty instrument slot: type byte 0xFF, zero-filled
        otherwise. `M8Block()` on its own is NOT an empty slot — its buffer
        is 0 bytes, which write() would zero-pad into a type-0x00 (WAVSYNTH)
        block. Use this (or `clear_slot`) instead of hand-building a block."""
        block = M8Block()
        block.data = bytearray([0xFF] + [0] * (BLOCK_SIZE - 1))
        return block

    def to_dict(self):
        """One entry per slot; None for empty or unparsed slots."""
        return [x.to_dict() if self.is_concrete(i) else None for i, x in enumerate(self)]

    def __repr__(self):
        used = [f"{i}: {type(x).__name__[2:]} {_label(x)!r}" for i, x in enumerate(self) if self.is_concrete(i)]
        if not used:
            return f"M8Instruments(none used of {len(self)})"
        return f"M8Instruments({len(used)} used of {len(self)}: " + ", ".join(used) + ")"

    def __init__(self, items=None):
        super().__init__()
        for item in (items or []):
            list.append(self, item)
        while len(self) < BLOCK_COUNT:
            list.append(self, self.empty_block())

    def clear_slot(self, index):
        """Empty a slot in place. The safe way to null out an instrument —
        assigning a bare `M8Block()` produces a phantom WAVSYNTH instead."""
        self[index] = self.empty_block()

    def is_concrete(self, index):
        """True if the slot holds a real, editable instrument — not an
        empty/unsupported-type M8Block placeholder (and not out of range)."""
        if not (0 <= index < len(self)):
            return False
        return not isinstance(self[index], M8Block)

    @classmethod
    def read(cls, data, version=None):
        # Eagerly import every concrete subclass so the registry is populated.
        from m8.api.instruments import sampler, wavsynth, macrosynth, fmsynth, external, midiout, hypersynth  # noqa: F401

        instance = cls.__new__(cls)
        list.__init__(instance)

        for i in range(BLOCK_COUNT):
            start = i * BLOCK_SIZE
            block_data = data[start:start + BLOCK_SIZE]
            instr_type = block_data[0]

            subclass = _INSTRUMENT_REGISTRY.get(instr_type)
            if subclass is not None:
                list.append(instance, subclass.read(block_data, version=version))
            elif instr_type == 0xFF:
                list.append(instance, M8Block.read(block_data))
            else:
                try:
                    type_name = M8InstrumentType(instr_type).name
                    msg = (
                        f"Instrument slot {i}: type {type_name} (0x{instr_type:02X}) "
                        "is not implemented; data will round-trip but cannot be edited"
                    )
                except ValueError:
                    msg = (
                        f"Instrument slot {i}: unknown type 0x{instr_type:02X}; "
                        "data will round-trip but cannot be edited"
                    )
                warnings.warn(msg, stacklevel=2)
                list.append(instance, M8Block.read(block_data))

        return instance

    def clone(self):
        instance = self.__class__.__new__(self.__class__)
        list.__init__(instance)
        for instr in self:
            list.append(instance, instr.clone() if hasattr(instr, "clone") else instr)
        return instance

    def write(self):
        result = bytearray()
        for instr in self:
            instr_data = instr.write() if hasattr(instr, "write") else b""
            if len(instr_data) < BLOCK_SIZE:
                # A short (or empty) block can never be a complete instrument;
                # treat it as an empty slot rather than zero-padding it into a
                # type-0x00 (WAVSYNTH) block.
                instr_data = bytes(self.empty_block().data)
            elif len(instr_data) > BLOCK_SIZE:
                instr_data = instr_data[:BLOCK_SIZE]
            result.extend(instr_data)
        return bytes(result)

