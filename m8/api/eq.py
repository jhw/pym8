# m8/api/eq.py
"""M8 EQ — 3-band parametric EQ records and the project-level EQ collection.

Layout follows m8-file-parser/src/eq.rs:

    EqBand    6 bytes  (mode_byte, freq_fin, freq, level_fin, level, q)
    Equ      18 bytes  (low + mid + high band, each 6 bytes)
    Eqs      M × 18 bytes at offset 0x1AD5A+4 in the project file

`mode_byte` packs the EQ type (low 3 bits) and stereo mode (bits 5-7).
`freq` + `freq_fin` form a 16-bit unsigned frequency value (Hz).
`level` + `level_fin` form a 16-bit signed gain × 100.

The project ships M EQs where M depends on firmware:
- v4.0:  36  (32 instrument + 3 effects + 1 global)
- v4.1+: 132 (128 instrument + 3 effects + 1 global)

pym8 targets v6.0+ so M = 132 — matches the bundled TEMPLATE-6-2-1.m8s
where EQ data extends to exactly EOF.

Per-instrument EQ binding is the `associated_eq` byte on each instrument
(byte 62 of the instrument block in v5.0+). It indexes into the project's
EQ list; 0xFF means "no EQ assigned".
"""

from enum import IntEnum

from m8.api.fields import ByteField, iter_fields


EQ_BAND_BYTES = 6
EQ_BANDS_PER_EQ = 3
EQ_BYTES = EQ_BAND_BYTES * EQ_BANDS_PER_EQ  # 18

# v4.1+ layout: 128 per-instrument + 3 effect-section + 1 global.
EQ_COUNT_V4_1 = 132
EQ_COUNT = EQ_COUNT_V4_1


class M8EqType(IntEnum):
    """EQ filter type (stored in low 3 bits of mode_byte)."""
    LOWCUT = 0
    LOWSHELF = 1
    BELL = 2
    BANDPASS = 3
    HISHELF = 4
    HICUT = 5
    ALLPASS = 6


class M8EqMode(IntEnum):
    """EQ stereo processing mode (stored in bits 5-7 of mode_byte)."""
    STEREO = 0
    MID = 1
    SIDE = 2
    LEFT = 3
    RIGHT = 4


class M8EqBand:
    """One band of a 3-band EQ. Six raw bytes; type and mode are packed.

    `eq_type` and `eq_mode` are properties that unpack `mode_byte` — set
    either and it updates the underlying byte. Set `mode_byte` directly to
    preserve unknown bits (the M8 firmware uses bits 3-4 for reserved
    state in some firmware versions; round-trip-faithful code goes through
    the raw byte).
    """

    BYTES = EQ_BAND_BYTES

    mode_byte  = ByteField(0)
    freq_fin   = ByteField(1)
    freq       = ByteField(2)
    level_fin  = ByteField(3)
    level      = ByteField(4)
    q          = ByteField(5)

    def __init__(self, **kwargs):
        self._data = bytearray(self.BYTES)
        for _, fld in iter_fields(type(self)):
            fld.apply_default(self)
        for key, value in kwargs.items():
            setattr(self, key, value)

    @property
    def eq_type(self):
        return self.mode_byte & 0x07

    @eq_type.setter
    def eq_type(self, value):
        if hasattr(value, "value"):
            value = value.value
        self.mode_byte = (self.mode_byte & 0xF8) | (int(value) & 0x07)

    @property
    def eq_mode(self):
        return (self.mode_byte >> 5) & 0x07

    @eq_mode.setter
    def eq_mode(self, value):
        if hasattr(value, "value"):
            value = value.value
        self.mode_byte = (self.mode_byte & 0x1F) | ((int(value) & 0x07) << 5)

    def frequency(self):
        """Combined 16-bit unsigned frequency."""
        return (self.freq << 8) | self.freq_fin

    def gain_db(self):
        """Combined 16-bit signed gain divided by 100 (dB)."""
        raw = (self.level << 8) | self.level_fin
        if raw >= 0x8000:
            raw -= 0x10000  # two's complement
        return raw / 100.0

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

    def __eq__(self, other):
        if not isinstance(other, M8EqBand):
            return NotImplemented
        return self._data == other._data

    def __repr__(self):
        try:
            t = M8EqType(self.eq_type).name
        except ValueError:
            t = f"0x{self.eq_type:02X}"
        try:
            m = M8EqMode(self.eq_mode).name
        except ValueError:
            m = f"0x{self.eq_mode:02X}"
        return f"M8EqBand({t}/{m}, freq={self.frequency()}, gain={self.gain_db():+.2f}dB, q={self.q})"

    def to_dict(self):
        try:
            type_name = M8EqType(self.eq_type).name
        except ValueError:
            type_name = self.eq_type
        try:
            mode_name = M8EqMode(self.eq_mode).name
        except ValueError:
            mode_name = self.eq_mode
        return {
            "eq_type": type_name,
            "eq_mode": mode_name,
            "freq": self.freq,
            "freq_fin": self.freq_fin,
            "level": self.level,
            "level_fin": self.level_fin,
            "q": self.q,
        }

    @classmethod
    def from_dict(cls, d):
        instance = cls()
        if "eq_type" in d:
            v = d["eq_type"]
            instance.eq_type = M8EqType[v].value if isinstance(v, str) else v
        if "eq_mode" in d:
            v = d["eq_mode"]
            instance.eq_mode = M8EqMode[v].value if isinstance(v, str) else v
        for key in ("freq", "freq_fin", "level", "level_fin", "q"):
            if key in d:
                setattr(instance, key, d[key])
        return instance


# Default band settings — match m8-file-parser EqBand::default_{low,mid,high}.
def _default_low_band():
    band = M8EqBand()
    band.eq_type = M8EqType.LOWSHELF
    band.eq_mode = M8EqMode.STEREO
    band.freq = 0  # 100 Hz = 0x0064; high byte = 0
    band.freq_fin = 0x64
    band.q = 50
    return band


def _default_mid_band():
    band = M8EqBand()
    band.eq_type = M8EqType.BELL
    band.eq_mode = M8EqMode.STEREO
    band.freq = 0x03  # 1000 Hz = 0x03E8
    band.freq_fin = 0xE8
    band.q = 50
    return band


def _default_high_band():
    band = M8EqBand()
    band.eq_type = M8EqType.HISHELF
    band.eq_mode = M8EqMode.STEREO
    band.freq = 0x13  # 5000 Hz = 0x1388
    band.freq_fin = 0x88
    band.q = 50
    return band


class M8Eq:
    """3-band parametric EQ (18 bytes: low + mid + high)."""

    BYTES = EQ_BYTES

    def __init__(self, low=None, mid=None, high=None):
        self.low = low if low is not None else _default_low_band()
        self.mid = mid if mid is not None else _default_mid_band()
        self.high = high if high is not None else _default_high_band()

    @classmethod
    def read(cls, data):
        return cls(
            low=M8EqBand.read(data[0:EQ_BAND_BYTES]),
            mid=M8EqBand.read(data[EQ_BAND_BYTES:EQ_BAND_BYTES * 2]),
            high=M8EqBand.read(data[EQ_BAND_BYTES * 2:EQ_BAND_BYTES * 3]),
        )

    def write(self):
        return self.low.write() + self.mid.write() + self.high.write()

    def clone(self):
        return M8Eq(low=self.low.clone(), mid=self.mid.clone(), high=self.high.clone())

    def __eq__(self, other):
        if not isinstance(other, M8Eq):
            return NotImplemented
        return self.low == other.low and self.mid == other.mid and self.high == other.high

    def is_default(self):
        """True if every band still matches the firmware defaults."""
        return (self.low == _default_low_band()
                and self.mid == _default_mid_band()
                and self.high == _default_high_band())

    def to_dict(self):
        return {"low": self.low.to_dict(), "mid": self.mid.to_dict(), "high": self.high.to_dict()}

    @classmethod
    def from_dict(cls, d):
        return cls(
            low=M8EqBand.from_dict(d.get("low", {})) if "low" in d else _default_low_band(),
            mid=M8EqBand.from_dict(d.get("mid", {})) if "mid" in d else _default_mid_band(),
            high=M8EqBand.from_dict(d.get("high", {})) if "high" in d else _default_high_band(),
        )


class M8Eqs(list):
    """Project-level EQ collection (132 entries in v6.0+).

    Index map by convention (matching m8-file-parser):
    -   0      : global (master) EQ
    -   1-3    : effect-section EQs (chorus, delay, reverb)
    -   4-131  : per-instrument EQs (referenced by instrument.associated_eq)

    `associated_eq = 0xFF` on an instrument means "no EQ assigned".
    """

    COUNT = EQ_COUNT
    TOTAL_BYTES = EQ_COUNT * EQ_BYTES

    def __init__(self):
        super().__init__()
        for _ in range(self.COUNT):
            self.append(M8Eq())

    @classmethod
    def read(cls, data, version=None):
        """Parse 132 consecutive M8Eq records from `data`.

        `version` reserved for the v4.0 → v4.1 split (32 → 128 instrument
        EQs); not consulted today because pym8 targets v6.0+.
        """
        instance = cls.__new__(cls)
        list.__init__(instance)
        for i in range(cls.COUNT):
            start = i * EQ_BYTES
            block = data[start:start + EQ_BYTES]
            if len(block) < EQ_BYTES:
                block = block + bytes(EQ_BYTES - len(block))
            instance.append(M8Eq.read(block))
        return instance

    def write(self):
        return b"".join(eq.write() for eq in self)

    def clone(self):
        instance = self.__class__.__new__(self.__class__)
        list.__init__(instance)
        for eq in self:
            instance.append(eq.clone())
        return instance

    def to_dict(self):
        return [eq.to_dict() for eq in self]

    @classmethod
    def from_dict(cls, items):
        instance = cls.__new__(cls)
        list.__init__(instance)
        for item in items[:cls.COUNT]:
            instance.append(M8Eq.from_dict(item))
        while len(instance) < cls.COUNT:
            instance.append(M8Eq())
        return instance
