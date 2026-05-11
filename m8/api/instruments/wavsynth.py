# m8/api/instruments/wavsynth.py
"""M8 WavSynth instrument."""

from enum import IntEnum

from m8.api.fields import ByteField
from m8.api.instrument import (
    M8FilterType,
    M8Instrument,
    M8InstrumentType,
    M8LimiterType,
)


class M8WavsynthModDest(IntEnum):
    """Wavsynth modulator destination parameters."""
    OFF = 0x00
    VOLUME = 0x01
    PITCH = 0x02
    SIZE = 0x03
    MULT = 0x04
    WARP = 0x05
    MIRROR = 0x06
    CUTOFF = 0x07
    RES = 0x08
    AMP = 0x09
    PAN = 0x0A


class M8WavShape(IntEnum):
    """WavSynth waveform shapes."""
    PULSE12 = 0
    PULSE25 = 1
    PULSE50 = 2
    PULSE75 = 3
    SAW = 4
    TRIANGLE = 5
    SINE = 6
    NOISE_PITCHED = 7
    NOISE = 8
    WT_CRUSH = 9
    WT_FOLDING = 10
    WT_FREQ = 11
    WT_FUZZY = 12
    WT_GHOST = 13
    WT_GRAPHIC = 14
    WT_LFOPLAY = 15
    WT_LIQUID = 16
    WT_MORPHING = 17
    WT_MYSTIC = 18
    WT_STICKY = 19
    WT_TIDAL = 20
    WT_TIDY = 21
    WT_TUBE = 22
    WT_UMBRELLA = 23
    WT_UNWIND = 24
    WT_VIRAL = 25
    WT_WAVES = 26
    WT_DRIP = 27
    WT_FROGGY = 28
    WT_INSONIC = 29
    WT_RADIUS = 30
    WT_SCRATCH = 31
    WT_SMOOTH = 32
    WT_WOBBLE = 33
    WT_ASIMMTRY = 34
    WT_BLEEN = 35
    WT_FRACTAL = 36
    WT_GENTLE = 37
    WT_HARMONIC = 38
    WT_HYPNOTIC = 39
    WT_ITERATIV = 40
    WT_MICROWAV = 41
    WT_PLAITS01 = 42
    WT_PLAITS02 = 43
    WT_RISEFALL = 44
    WT_TONAL = 45
    WT_TWINE = 46
    WT_ALIEN = 47
    WT_CYBERNET = 48
    WT_DISORDR = 49
    WT_FORMANT = 50
    WT_HYPER = 51
    WT_JAGGED = 52
    WT_MIXED = 53
    WT_MULTIPLY = 54
    WT_NOWHERE = 55
    WT_PINBALL = 56
    WT_RINGS = 57
    WT_SHIMMER = 58
    WT_SPECTRAL = 59
    WT_SPOOKY = 60
    WT_TRANSFRM = 61
    WT_TWISTED = 62
    WT_VOCAL = 63
    WT_WASHED = 64
    WT_WONDER = 65
    WT_WOWEE = 66
    WT_ZAP = 67
    WT_BRAIDS = 68
    WT_VOXSYNTH = 69


class M8Wavsynth(M8Instrument):
    """Wavetable synthesizer."""

    TYPE_ID = M8InstrumentType.WAVSYNTH
    MOD_DEST_ENUM_CLASS = M8WavsynthModDest

    transpose    = ByteField(13)
    table_tick   = ByteField(14)
    volume       = ByteField(15)
    pitch        = ByteField(16)
    fine_tune    = ByteField(17, default=0x80)

    shape        = ByteField(18, enum=M8WavShape)
    size         = ByteField(19, default=0x20)
    mult         = ByteField(20)
    warp         = ByteField(21)
    mirror       = ByteField(22)

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
