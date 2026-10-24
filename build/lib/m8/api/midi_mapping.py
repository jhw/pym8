# m8/api/midi_mapping.py
"""M8 MIDI controller mappings.

128 mappings × 7 bytes at file offset 0x1A5FE (108030). Layout follows
m8-file-parser/src/settings.rs::MidiMapping.

Each mapping ties an incoming MIDI CC message (channel + control number)
to an internal M8 parameter (type + param_index) with min/max scaling.
An "empty" mapping is conventionally one where channel == 0 (per the
Rust `is_empty` helper).

The seven bytes:
  byte 0  channel         MIDI channel (0 = empty / disabled)
  byte 1  control_number  CC number being mapped
  byte 2  value           current value (sent back to controller on init?)
  byte 3  typ             target parameter type
  byte 4  param_index     index within the target type
  byte 5  min_value       low end of the scaling range
  byte 6  max_value       high end of the scaling range
"""

from m8.api.fields import ByteField, iter_fields


MIDI_MAPPING_BYTES = 7
MIDI_MAPPING_COUNT = 128


class M8MidiMapping:
    """One MIDI controller → M8 parameter mapping. 7 bytes."""

    BYTES = MIDI_MAPPING_BYTES

    channel        = ByteField(0)
    control_number = ByteField(1)
    value          = ByteField(2)
    typ            = ByteField(3)
    param_index    = ByteField(4)
    min_value      = ByteField(5)
    max_value      = ByteField(6)

    def __init__(self, **kwargs):
        self._data = bytearray(self.BYTES)
        for _, fld in iter_fields(type(self)):
            fld.apply_default(self)
        for key, value in kwargs.items():
            setattr(self, key, value)

    def is_empty(self):
        """Convention: channel == 0 means this mapping slot is unused."""
        return self.channel == 0

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
        return {name: fld.to_dict(self) for name, fld in iter_fields(type(self))}

    @classmethod
    def from_dict(cls, d):
        instance = cls()
        fields_by_name = {name: fld for name, fld in iter_fields(cls)}
        for key, value in d.items():
            fld = fields_by_name.get(key)
            if fld is not None:
                fld.from_dict(instance, value)
        return instance


class M8MidiMappings(list):
    """128 MIDI controller mappings."""

    COUNT = MIDI_MAPPING_COUNT
    TOTAL_BYTES = MIDI_MAPPING_COUNT * MIDI_MAPPING_BYTES

    def __init__(self):
        super().__init__()
        for _ in range(self.COUNT):
            self.append(M8MidiMapping())

    @classmethod
    def read(cls, data, version=None):
        instance = cls.__new__(cls)
        list.__init__(instance)
        for i in range(cls.COUNT):
            start = i * MIDI_MAPPING_BYTES
            block = data[start:start + MIDI_MAPPING_BYTES]
            if len(block) < MIDI_MAPPING_BYTES:
                block = block + bytes(MIDI_MAPPING_BYTES - len(block))
            instance.append(M8MidiMapping.read(block))
        return instance

    def write(self):
        return b"".join(m.write() for m in self)

    def clone(self):
        instance = self.__class__.__new__(self.__class__)
        list.__init__(instance)
        for m in self:
            instance.append(m.clone())
        return instance

    def to_dict(self):
        return [m.to_dict() for m in self]

    @classmethod
    def from_dict(cls, items):
        instance = cls.__new__(cls)
        list.__init__(instance)
        for item in items[:cls.COUNT]:
            instance.append(M8MidiMapping.from_dict(item))
        while len(instance) < cls.COUNT:
            instance.append(M8MidiMapping())
        return instance
