# m8/api/instruments/sampler.py
"""M8 Sampler instrument."""

from enum import IntEnum

from m8.api.fields import ByteField, StringField
from m8.api.instrument import (
    M8FilterType,
    M8Instrument,
    M8InstrumentType,
    M8LimiterType,
)


SAMPLE_PATH_OFFSET = 87
SAMPLE_PATH_SIZE = 128


class M8PlayMode(IntEnum):
    """Sampler playback modes."""
    FWD = 0x00
    REV = 0x01
    FWDLOOP = 0x02
    REVLOOP = 0x03
    FWD_PP = 0x04
    REV_PP = 0x05
    OSC = 0x06
    OSC_REV = 0x07
    OSC_PP = 0x08
    REPITCH = 0x09
    REP_REV = 0x0A
    REP_PP = 0x0B
    REP_BPM = 0x0C
    BPM_REV = 0x0D
    BPM_PP = 0x0E


class M8SamplerModDest(IntEnum):
    """Sampler modulator destinations."""
    OFF = 0x00
    VOLUME = 0x01
    PITCH = 0x02
    LOOP_ST = 0x03
    LENGTH = 0x04
    DEGRADE = 0x05
    CUTOFF = 0x06
    RES = 0x07
    AMP = 0x08
    PAN = 0x09


class M8Sampler(M8Instrument):
    """Sample playback instrument."""

    TYPE_ID = M8InstrumentType.SAMPLER
    MOD_DEST_ENUM_CLASS = M8SamplerModDest

    transpose    = ByteField(13)
    table_tick   = ByteField(14)
    volume       = ByteField(15)
    pitch        = ByteField(16)
    fine_tune    = ByteField(17, default=0x80)

    play_mode    = ByteField(18, enum=M8PlayMode)
    slice        = ByteField(19)
    start        = ByteField(20)
    loop_start   = ByteField(21)
    length       = ByteField(22, default=0xFF)
    degrade      = ByteField(23)

    filter_type  = ByteField(24, enum=M8FilterType)
    cutoff       = ByteField(25, default=0xFF)
    resonance    = ByteField(26)

    amp          = ByteField(27)
    limit        = ByteField(28, enum=M8LimiterType)
    pan          = ByteField(29, default=0x80)
    dry          = ByteField(30, default=0xC0)
    chorus_send  = ByteField(31)
    delay_send   = ByteField(32)
    reverb_send  = ByteField(33)

    sample_path  = StringField(SAMPLE_PATH_OFFSET, SAMPLE_PATH_SIZE)
