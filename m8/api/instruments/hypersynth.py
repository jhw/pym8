# m8/api/instruments/hypersynth.py
"""M8 HyperSynth instrument (type 5) — 6-oscillator detuned-stack synth
with a 16-slot chord matrix.

Layout follows m8-file-parser/src/instruments/hypersynth.rs:

  byte  0       type byte (0x05)
  bytes 1-12    name
  byte  13      transpose (in firmware 6.0+ this byte packs transpose into
                bit 7 and associated_eq into bits 0-6; pym8 doesn't model EQ
                yet so the byte is preserved verbatim)
  byte  14      table_tick
  byte  15      volume
  byte  16      pitch
  byte  17      fine_tune
  bytes 18-24   default_chord (7 semitone offsets — what plays when no chord
                slot is engaged)
  byte  25      scale
  byte  26      shift
  byte  27      swarm
  byte  28      width
  byte  29      subosc
  byte  30      filter_type
  byte  31      cutoff
  byte  32      resonance
  byte  33      amp
  byte  34      limit
  byte  35      pan
  byte  36      dry
  byte  37      chorus_send
  byte  38      delay_send
  byte  39      reverb_send
  bytes 40-62   reserved / EQ byte (preserved as raw bytes)
  bytes 63-86   modulators (4 × 6 bytes, standard)
  bytes 87-198  chords (16 × 7 bytes — mask + 6 offsets each)
  bytes 199-214 trailing pad (preserved)
"""

from enum import IntEnum

from m8.api.fields import ByteField, BytesField
from m8.api.instrument import (
    M8FilterType,
    M8Instrument,
    M8InstrumentType,
    M8LimiterType,
)


CHORDS_OFFSET = 87
CHORD_COUNT = 16
CHORD_BYTES = 7  # 1 mask byte + 6 oscillator offsets
CHORD_OSC_COUNT = 6


class M8HyperSynthModDest(IntEnum):
    """HyperSynth modulator destinations.

    Mirrors hypersynth.rs DESTINATIONS — note SHIFT/SWARM/WIDTH/SUBOSC are
    HyperSynth-specific, replacing slots that other synths use for shape/etc.
    """
    OFF = 0x00
    VOLUME = 0x01
    PITCH = 0x02
    SHIFT = 0x03
    SWARM = 0x04
    WIDTH = 0x05
    SUBOSC = 0x06
    CUTOFF = 0x07
    RES = 0x08
    AMP = 0x09
    PAN = 0x0A
    MOD_AMT = 0x0B
    MOD_RATE = 0x0C
    MOD_BOTH = 0x0D
    MOD_BINV = 0x0E


class M8Chord:
    """One row in a HyperSynth chord matrix.

    A chord is a bitmask (which of the 6 oscillators play) plus 6 semitone
    offsets (one per oscillator, only meaningful for oscillators enabled in
    the mask). Pressing a chord slot on the M8 plays the default note +
    each enabled oscillator's offset simultaneously.
    """

    __slots__ = ("mask", "offsets")

    def __init__(self, mask=0, offsets=None):
        self.mask = mask & 0xFF
        if offsets is None:
            self.offsets = [0] * CHORD_OSC_COUNT
        else:
            self.offsets = [int(o) & 0xFF for o in offsets]
            if len(self.offsets) != CHORD_OSC_COUNT:
                raise ValueError(
                    f"M8Chord needs {CHORD_OSC_COUNT} offsets, got {len(self.offsets)}"
                )

    @classmethod
    def read(cls, data):
        return cls(mask=data[0], offsets=list(data[1:CHORD_BYTES]))

    def write(self):
        return bytes([self.mask] + self.offsets)

    def is_osc_on(self, osc):
        """Whether oscillator `osc` (0-5) plays in this chord."""
        if not 0 <= osc < CHORD_OSC_COUNT:
            raise IndexError(f"oscillator index {osc} out of range [0, {CHORD_OSC_COUNT - 1}]")
        return bool(self.mask & (1 << osc))

    def clone(self):
        return M8Chord(mask=self.mask, offsets=list(self.offsets))

    def __eq__(self, other):
        if not isinstance(other, M8Chord):
            return NotImplemented
        return self.mask == other.mask and self.offsets == other.offsets

    def __repr__(self):
        return f"M8Chord(mask=0x{self.mask:02X}, offsets={self.offsets})"

    def to_dict(self):
        return {"mask": self.mask, "offsets": list(self.offsets)}

    @classmethod
    def from_dict(cls, data):
        return cls(mask=data.get("mask", 0), offsets=data.get("offsets", [0] * CHORD_OSC_COUNT))


class M8HyperSynthChords(list):
    """The 16 chord rows on a HyperSynth (mutable list of M8Chord)."""

    COUNT = CHORD_COUNT
    TOTAL_BYTES = CHORD_COUNT * CHORD_BYTES

    def __init__(self):
        super().__init__()
        for _ in range(self.COUNT):
            self.append(M8Chord())

    @classmethod
    def read(cls, data):
        instance = cls.__new__(cls)
        list.__init__(instance)
        for i in range(cls.COUNT):
            start = i * CHORD_BYTES
            block = data[start:start + CHORD_BYTES]
            if len(block) < CHORD_BYTES:
                block = block + bytes(CHORD_BYTES - len(block))
            instance.append(M8Chord.read(block))
        return instance

    def write(self):
        result = bytearray()
        for chord in self:
            chord_bytes = chord.write()
            if len(chord_bytes) < CHORD_BYTES:
                chord_bytes = chord_bytes + bytes(CHORD_BYTES - len(chord_bytes))
            result.extend(chord_bytes[:CHORD_BYTES])
        return bytes(result)

    def clone(self):
        instance = self.__class__.__new__(self.__class__)
        list.__init__(instance)
        for chord in self:
            instance.append(chord.clone())
        return instance

    def to_dict(self):
        return [c.to_dict() for c in self]

    @classmethod
    def from_dict(cls, items):
        instance = cls.__new__(cls)
        list.__init__(instance)
        for item in items[:cls.COUNT]:
            instance.append(M8Chord.from_dict(item))
        while len(instance) < cls.COUNT:
            instance.append(M8Chord())
        return instance


class M8HyperSynth(M8Instrument):
    """6-oscillator detuned-stack synth with a 16-slot chord matrix."""

    TYPE_ID = M8InstrumentType.HYPERSYNTH
    MOD_DEST_ENUM_CLASS = M8HyperSynthModDest

    transpose      = ByteField(13)
    table_tick     = ByteField(14)
    volume         = ByteField(15)
    pitch          = ByteField(16)
    fine_tune      = ByteField(17, default=0x80)

    default_chord  = BytesField(18, length=7)

    scale          = ByteField(25)
    shift          = ByteField(26)
    swarm          = ByteField(27)
    width          = ByteField(28)
    subosc         = ByteField(29)

    filter_type    = ByteField(30, enum=M8FilterType)
    cutoff         = ByteField(31, default=0xFF)
    resonance      = ByteField(32)

    amp            = ByteField(33)
    limit          = ByteField(34, enum=M8LimiterType)
    pan            = ByteField(35, default=0x80)
    dry            = ByteField(36, default=0xC0)
    chorus_send    = ByteField(37)
    delay_send     = ByteField(38)
    reverb_send    = ByteField(39)

    def __init__(self, **kwargs):
        # Pop chord kwargs so the base __init__ (which setattrs every kwarg)
        # doesn't try to resolve `chords` against a non-existent descriptor.
        chords = kwargs.pop("chords", None)
        super().__init__(**kwargs)
        self.chords = chords if chords is not None else M8HyperSynthChords()

    def write(self):
        buffer = bytearray(super().write())
        chord_data = self.chords.write()
        buffer[CHORDS_OFFSET:CHORDS_OFFSET + len(chord_data)] = chord_data
        return bytes(buffer)

    @classmethod
    def read(cls, data):
        instance = super().read(data)
        chord_region = data[CHORDS_OFFSET:CHORDS_OFFSET + M8HyperSynthChords.TOTAL_BYTES]
        instance.chords = M8HyperSynthChords.read(chord_region)
        return instance

    def clone(self):
        instance = super().clone()
        instance.chords = self.chords.clone()
        return instance

    def to_dict(self):
        result = super().to_dict()
        result["chords"] = self.chords.to_dict()
        return result

    @classmethod
    def from_dict(cls, params):
        # Base from_dict walks params["params"] (a sub-dict); top-level
        # "chords" doesn't interfere, so we can let it through unchanged
        # and graft chords on after.
        instance = super().from_dict(params)
        if "chords" in params:
            instance.chords = M8HyperSynthChords.from_dict(params["chords"])
        return instance
