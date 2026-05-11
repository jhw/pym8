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
from m8.api.fields import ByteField, StringField, iter_fields
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
        instance.version = M8Version(self.version.major, self.version.minor, self.version.patch)
        instance.modulators = self.modulators.clone()
        return instance

    @classmethod
    def read(cls, data):
        """Parse a single instrument block from binary."""
        instance = cls.__new__(cls)
        instance._data = bytearray(data[:BLOCK_SIZE])
        instance.version = M8Version()
        instance.modulators = M8Modulators.read(data[MODULATORS_OFFSET:])
        return instance

    @classmethod
    def read_from_file(cls, file_path):
        """Read an .m8i single-instrument file.

        M8i files have:
        - Metadata header at byte 0
        - Version at byte 10
        - Instrument data at byte 14 (the metadata offset constant)
        - Modulators at instrument-offset 61 in an M8i-specific layout
          (instead of offset 63 used in M8s project files)
        """
        from m8.api.metadata import METADATA_OFFSET
        # Eagerly import every subclass so the registry is populated.
        from m8.api.instruments import sampler, wavsynth, macrosynth, fmsynth, external, midiout  # noqa: F401

        with open(file_path, "rb") as f:
            data = f.read()

        version = M8Version.read(data[10:])
        instrument_data = data[METADATA_OFFSET:]
        instr_type = instrument_data[TYPE_OFFSET]

        subclass = _INSTRUMENT_REGISTRY.get(instr_type)
        if subclass is None:
            raise ValueError(f"Unsupported instrument type 0x{instr_type:02X} in {file_path}")

        instance = subclass.read(instrument_data)
        instance.version = version
        # M8i modulators are at offset 61 and use a different parameter order
        # for LFO modulators — convert to the M8s in-memory layout.
        instance.modulators = M8Modulators.read_m8i(instrument_data[61:])
        return instance

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
            from m8.api.instruments import sampler, wavsynth, macrosynth, fmsynth, external, midiout  # noqa: F401

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


class M8Instruments(list):
    """The 128-slot instrument collection inside a project."""

    def __init__(self, items=None):
        super().__init__()
        for item in (items or []):
            self.append(item)
        while len(self) < BLOCK_COUNT:
            empty = M8Block()
            empty.data = bytearray([0xFF] + [0] * (BLOCK_SIZE - 1))
            self.append(empty)

    @classmethod
    def read(cls, data):
        # Eagerly import every concrete subclass so the registry is populated.
        from m8.api.instruments import sampler, wavsynth, macrosynth, fmsynth, external, midiout  # noqa: F401

        instance = cls.__new__(cls)
        list.__init__(instance)

        for i in range(BLOCK_COUNT):
            start = i * BLOCK_SIZE
            block_data = data[start:start + BLOCK_SIZE]
            instr_type = block_data[0]

            subclass = _INSTRUMENT_REGISTRY.get(instr_type)
            if subclass is not None:
                instance.append(subclass.read(block_data))
            elif instr_type == 0xFF:
                instance.append(M8Block.read(block_data))
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
                instance.append(M8Block.read(block_data))

        return instance

    def clone(self):
        instance = self.__class__.__new__(self.__class__)
        list.__init__(instance)
        for instr in self:
            instance.append(instr.clone() if hasattr(instr, "clone") else instr)
        return instance

    def write(self):
        result = bytearray()
        for instr in self:
            instr_data = instr.write() if hasattr(instr, "write") else bytes([0] * BLOCK_SIZE)
            if len(instr_data) < BLOCK_SIZE:
                instr_data = instr_data + bytes([0] * (BLOCK_SIZE - len(instr_data)))
            elif len(instr_data) > BLOCK_SIZE:
                instr_data = instr_data[:BLOCK_SIZE]
            result.extend(instr_data)
        return bytes(result)

    def validate(self):
        if len(self) > BLOCK_COUNT:
            raise ValueError(f"Too many instruments: {len(self)}, maximum is {BLOCK_COUNT}")
