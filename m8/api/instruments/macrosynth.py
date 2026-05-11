# m8/api/instruments/macrosynth.py
"""M8 MacroSynth instrument (Braids-based)."""

from enum import IntEnum

from m8.api.fields import ByteField
from m8.api.instrument import (
    M8FilterType,
    M8Instrument,
    M8InstrumentType,
    M8LimiterType,
)


class M8MacrosynthModDest(IntEnum):
    """Macrosynth modulator destinations."""
    OFF = 0x00
    VOLUME = 0x01
    PITCH = 0x02
    TIMBRE = 0x03
    COLOUR = 0x04
    DEGRADE = 0x05
    REDUX = 0x06
    CUTOFF = 0x07
    RES = 0x08
    AMP = 0x09
    PAN = 0x0A


class M8MacroShape(IntEnum):
    """MacroSynth oscillator shapes (Mutable Instruments Braids algorithms)."""
    CSAW = 0
    MORPH = 1
    SAW_SQUARE = 2
    FOLD = 3
    SQUARE = 4
    SYN_SAW = 5
    SYN_SQUARE = 6
    SAW_SWARM = 7
    SQUARE_SWARM = 8
    TRI_SWARM = 9
    SIN_SWARM = 10
    RING = 11
    SAW_STACK = 12
    SAW_WAVE = 13
    TOY = 14
    ZLPF = 15
    ZPKF = 16
    ZBPF = 17
    ZHPF = 18
    VOSM = 19
    VOWL = 20
    VFOF = 21
    HARM = 22
    FM = 23
    FBFM = 24
    WTFM = 25
    PLUK = 26
    BOWD = 27
    BLOW = 28
    FLUT = 29
    BELL = 30
    DRUM = 31
    KICK = 32
    CYMB = 33
    SNAR = 34
    WTBL = 35
    WMAP = 36
    WLIN = 37
    WTX4 = 38
    NOIS = 39
    TWNQ = 40
    CLKN = 41
    CLOU = 42
    PRTC = 43
    QPSK = 44


class M8Macrosynth(M8Instrument):
    """Braids-based macro-oscillator synth."""

    TYPE_ID = M8InstrumentType.MACROSYNTH
    MOD_DEST_ENUM_CLASS = M8MacrosynthModDest

    transpose    = ByteField(13)
    table_tick   = ByteField(14)
    volume       = ByteField(15)
    pitch        = ByteField(16)
    fine_tune    = ByteField(17, default=0x80)

    shape        = ByteField(18, enum=M8MacroShape)
    timbre       = ByteField(19, default=0x80)
    colour       = ByteField(20, default=0x80)
    degrade      = ByteField(21)
    redux        = ByteField(22)

    filter_type  = ByteField(23, enum=M8FilterType)
    cutoff       = ByteField(24, default=0xFF)
    resonance    = ByteField(25)

    amp          = ByteField(26)
    limit        = ByteField(27, enum=M8LimiterType)
    pan          = ByteField(28, default=0x80)
    dry          = ByteField(29, default=0xC0)
    chorus_send  = ByteField(30)
    delay_send   = ByteField(31)
    reverb_send  = ByteField(32)
