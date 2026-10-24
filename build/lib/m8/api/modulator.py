# m8/api/modulator.py
"""M8 modulators — one subclass per modulator type, using the ByteField
descriptor framework for typed parameter access.

Each modulator slot in an instrument is one of 6 types (AHD, ADSR, Drum,
LFO, Trig, Tracking). Layout per slot is 6 bytes: type/destination nibbles
in byte 0, amount in byte 1, then type-specific parameters in bytes 2-5.

Changing the type of a modulator slot means replacing the slot, not mutating
in place — different types reinterpret bytes 2-5 differently.
"""

from enum import IntEnum

from m8.api.fields import ByteField, iter_fields


MODULATOR_BLOCK_SIZE = 6
MODULATOR_COUNT = 4

BLOCK_SIZE = MODULATOR_BLOCK_SIZE
BLOCK_COUNT = MODULATOR_COUNT

TYPE_DEST_OFFSET = 0
AMOUNT_OFFSET = 1


class M8ModulatorType(IntEnum):
    AHD_ENVELOPE = 0
    ADSR_ENVELOPE = 1
    DRUM_ENVELOPE = 2
    LFO = 3
    TRIG_ENVELOPE = 4
    TRACKING_ENVELOPE = 5


class M8LFOShape(IntEnum):
    """LFO oscillator waveform shapes."""
    TRI = 0x00
    SIN = 0x01
    RAMP_DOWN = 0x02
    RAMP_UP = 0x03
    EXP_DN = 0x04
    EXP_UP = 0x05
    SQR_DN = 0x06
    SQR_UP = 0x07
    RANDOM = 0x08
    DRUNK = 0x09
    TRI_T = 0x0A
    SIN_T = 0x0B
    RAMPD_T = 0x0C
    RAMPU_T = 0x0D
    EXPD_T = 0x0E
    EXPU_T = 0x0F
    SQ_D_T = 0x10
    SQ_U_T = 0x11
    RAND_T = 0x12
    DRNK_T = 0x13


class M8LFOTriggerMode(IntEnum):
    FREE = 0x00
    RETRIG = 0x01
    HOLD = 0x02
    ONCE = 0x03


_MODULATOR_REGISTRY = {}


class M8Modulator:
    """Base modulator. Subclasses declare type-specific descriptor fields.

    Byte 0 carries the type (high nibble) and destination (low nibble); byte 1
    is the modulation amount. Bytes 2-5 are type-specific.
    """

    MOD_TYPE = None  # subclasses override with a M8ModulatorType member

    amount = ByteField(AMOUNT_OFFSET, default=0xFF)

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if cls.MOD_TYPE is not None:
            _MODULATOR_REGISTRY[int(cls.MOD_TYPE)] = cls

    def __init__(self, destination=0, **kwargs):
        if self.MOD_TYPE is None:
            raise TypeError(f"{type(self).__name__} must declare MOD_TYPE")
        self._data = bytearray(BLOCK_SIZE)
        self._data[TYPE_DEST_OFFSET] = (int(self.MOD_TYPE) << 4) & 0xF0
        for _, fld in iter_fields(type(self)):
            fld.apply_default(self)
        if destination:
            self.destination = destination
        for key, value in kwargs.items():
            setattr(self, key, value)

    @property
    def mod_type(self):
        return (self._data[TYPE_DEST_OFFSET] >> 4) & 0x0F

    @property
    def destination(self):
        return self._data[TYPE_DEST_OFFSET] & 0x0F

    @destination.setter
    def destination(self, value):
        if hasattr(value, "value"):
            value = value.value
        value = int(value) & 0x0F
        self._data[TYPE_DEST_OFFSET] = (self._data[TYPE_DEST_OFFSET] & 0xF0) | value

    def write(self):
        return bytes(self._data)

    def clone(self):
        instance = self.__class__.__new__(self.__class__)
        instance._data = bytearray(self._data)
        return instance

    @classmethod
    def read(cls, data):
        """Read this specific modulator subclass from 6 bytes."""
        instance = cls.__new__(cls)
        instance._data = bytearray(data[:BLOCK_SIZE])
        return instance

    def to_dict(self, dest_enum_class=None):
        destination = self.destination
        if dest_enum_class is not None:
            try:
                destination = dest_enum_class(destination).name
            except (ValueError, KeyError):
                pass

        result = {
            "type": self.MOD_TYPE.name,
            "destination": destination,
            "amount": self.amount,
            "params": {},
        }
        for name, fld in iter_fields(type(self)):
            if name == "amount":
                continue
            result["params"][name] = fld.to_dict(self)
        return result

    @classmethod
    def from_dict(cls, params, dest_enum_class=None):
        """Reconstruct a modulator from a dict.

        Called on M8Modulator (the base), dispatches to the right subclass
        based on the `type` field. Called on a subclass, decodes directly.
        """
        if cls is M8Modulator:
            type_value = params.get("type", "AHD_ENVELOPE")
            if isinstance(type_value, str):
                try:
                    type_id = M8ModulatorType[type_value].value
                except KeyError:
                    type_id = 0
            else:
                type_id = int(type_value)
            subclass = _MODULATOR_REGISTRY.get(type_id, M8AHDModulator)
            return subclass.from_dict(params, dest_enum_class=dest_enum_class)

        instance = cls()
        if "destination" in params:
            d = params["destination"]
            if isinstance(d, str) and dest_enum_class is not None:
                try:
                    d = dest_enum_class[d].value
                except KeyError:
                    d = 0
            instance.destination = d
        if "amount" in params:
            instance.amount = params["amount"]

        fields_by_name = {n: f for n, f in iter_fields(cls)}
        for key, value in params.get("params", {}).items():
            fld = fields_by_name.get(key)
            if fld is None:
                continue
            fld.from_dict(instance, value)
        return instance


class M8AHDModulator(M8Modulator):
    """Attack/Hold/Decay envelope."""
    MOD_TYPE = M8ModulatorType.AHD_ENVELOPE
    attack = ByteField(2)
    hold = ByteField(3)
    decay = ByteField(4, default=0x80)


class M8ADSRModulator(M8Modulator):
    """Attack/Decay/Sustain/Release envelope."""
    MOD_TYPE = M8ModulatorType.ADSR_ENVELOPE
    attack = ByteField(2)
    decay = ByteField(3)
    sustain = ByteField(4)
    release = ByteField(5)


class M8DrumModulator(M8Modulator):
    """Drum envelope (Peak/Body/Decay)."""
    MOD_TYPE = M8ModulatorType.DRUM_ENVELOPE
    peak = ByteField(2)
    body = ByteField(3)
    decay = ByteField(4)


class M8LFOModulator(M8Modulator):
    """Low-Frequency Oscillator."""
    MOD_TYPE = M8ModulatorType.LFO
    shape = ByteField(2, enum=M8LFOShape)
    trigger_mode = ByteField(3, enum=M8LFOTriggerMode)
    freq = ByteField(4, default=0x10)
    retrigger = ByteField(5)


class M8TrigModulator(M8Modulator):
    """Trigger envelope (Attack/Hold/Decay/Source)."""
    MOD_TYPE = M8ModulatorType.TRIG_ENVELOPE
    attack = ByteField(2)
    hold = ByteField(3)
    decay = ByteField(4)
    src = ByteField(5)


class M8TrackingModulator(M8Modulator):
    """Tracking envelope (Source/LowValue/HighValue)."""
    MOD_TYPE = M8ModulatorType.TRACKING_ENVELOPE
    src = ByteField(2)
    lval = ByteField(3)
    hval = ByteField(4)


# Default modulator layout for a fresh instrument: 2 AHD, 2 LFO.
_DEFAULT_MODULATOR_CLASSES = [
    M8AHDModulator, M8AHDModulator, M8LFOModulator, M8LFOModulator,
]


class M8Modulators(list):
    """4 modulator slots within an instrument."""

    def __init__(self):
        super().__init__()
        for klass in _DEFAULT_MODULATOR_CLASSES:
            self.append(klass())

    @classmethod
    def read(cls, data):
        """Parse 4 modulators, dispatching on the type nibble of each slot."""
        instance = cls.__new__(cls)
        list.__init__(instance)
        for i in range(BLOCK_COUNT):
            start = i * BLOCK_SIZE
            block = data[start:start + BLOCK_SIZE]
            if len(block) < BLOCK_SIZE:
                block = block + bytes(BLOCK_SIZE - len(block))
            type_id = (block[0] >> 4) & 0x0F
            subclass = _MODULATOR_REGISTRY.get(type_id, M8AHDModulator)
            instance.append(subclass.read(block))
        return instance

    @classmethod
    def read_m8i(cls, data):
        """Read modulators from M8i format (different layout) and convert.

        M8i lacks explicit type bytes — it uses position in the slot list:
        slots 0-1 are AHD, slots 2-3 are LFO. M8i LFO byte ordering also
        differs from M8s and must be reordered.
        """
        instance = cls.__new__(cls)
        list.__init__(instance)
        for i in range(BLOCK_COUNT):
            start = i * BLOCK_SIZE
            block = data[start:start + BLOCK_SIZE]
            if len(block) < BLOCK_SIZE:
                block = block + bytes(BLOCK_SIZE - len(block))
            klass = _DEFAULT_MODULATOR_CLASSES[i]
            instance.append(_read_m8i_block(klass, block))
        return instance

    def clone(self):
        instance = self.__class__.__new__(self.__class__)
        list.__init__(instance)
        for mod in self:
            instance.append(mod.clone())
        return instance

    def to_dict(self, dest_enum_class=None):
        return [mod.to_dict(dest_enum_class=dest_enum_class) for mod in self]

    @classmethod
    def from_dict(cls, modulators_list, dest_enum_class=None):
        instance = cls.__new__(cls)
        list.__init__(instance)
        for mod_params in modulators_list:
            instance.append(M8Modulator.from_dict(mod_params, dest_enum_class=dest_enum_class))
        while len(instance) < BLOCK_COUNT:
            instance.append(_DEFAULT_MODULATOR_CLASSES[len(instance)]())
        return instance

    def write(self):
        result = bytearray()
        for mod in self:
            data = mod.write()
            if len(data) < BLOCK_SIZE:
                data = data + bytes(BLOCK_SIZE - len(data))
            elif len(data) > BLOCK_SIZE:
                data = data[:BLOCK_SIZE]
            result.extend(data)
        return bytes(result)


def _read_m8i_block(klass, block):
    """Translate one M8i modulator block to M8s layout and instantiate."""
    m8s = bytearray(BLOCK_SIZE)
    type_id = int(klass.MOD_TYPE)

    if klass is M8AHDModulator:
        # M8i AHD: dest, amt, atk, hold, dec, ?
        # M8s AHD: type+dest, amt, atk, hold, dec, ?
        dest = block[0]
        m8s[0] = (type_id << 4) | (dest & 0x0F)
        m8s[1:] = block[1:]
    elif klass is M8LFOModulator:
        # M8i LFO: osc, dest, trig, freq, amt, retrig
        # M8s LFO: type+dest, amt, osc, trig, freq, retrig
        osc, dest, trig, freq, amt, retrig = block
        m8s[0] = (type_id << 4) | (dest & 0x0F)
        m8s[1] = amt
        m8s[2] = osc
        m8s[3] = trig
        m8s[4] = freq
        m8s[5] = retrig
    else:
        dest = block[0]
        m8s[0] = (type_id << 4) | (dest & 0x0F)
        m8s[1:] = block[1:]

    return klass.read(bytes(m8s))
