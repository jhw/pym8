# m8/api/instruments/external.py
"""M8 External instrument (type 6) — audio input + 4 MIDI CC slots.

Distinct from M8MIDIOut (type 3). External instruments route audio through
M8 effects and can send a limited set of 4 MIDI CCs. For pure MIDI sequencing
to external gear, use M8MIDIOut instead.
"""

from enum import IntEnum

from m8.api.fields import ByteField
from m8.api.instrument import (
    M8FilterType,
    M8Instrument,
    M8InstrumentType,
    M8LimiterType,
)


class M8ExternalInput(IntEnum):
    """Audio input source for the External instrument's monitoring path."""
    OFF = 0x00
    LINE_IN_L = 0x01
    LINE_IN_R = 0x02
    LINE_IN_LR = 0x03


class M8ExternalPort(IntEnum):
    """MIDI output port for the External instrument."""
    DISABLED = 0x00
    USB = 0x01
    MIDI = 0x02
    USB_MIDI = 0x03


class M8ExternalModDest(IntEnum):
    """External-instrument modulator destinations."""
    OFF = 0x00
    VOLUME = 0x01
    CUTOFF = 0x02
    RES = 0x03
    AMP = 0x04
    PAN = 0x05
    CCA = 0x06
    CCB = 0x07
    CCC = 0x08
    CCD = 0x09
    MOD_AMT = 0x0A
    MOD_RATE = 0x0B
    MOD_BOTH = 0x0C
    MOD_BINV = 0x0D


class M8External(M8Instrument):
    """External-audio instrument with 4 MIDI CC slots (type 6)."""

    TYPE_ID = M8InstrumentType.EXTERNAL
    MOD_DEST_ENUM_CLASS = M8ExternalModDest

    transpose    = ByteField(13)
    table_tick   = ByteField(14)
    volume       = ByteField(15)
    pitch        = ByteField(16)
    fine_tune    = ByteField(17, default=0x80)

    input        = ByteField(18, enum=M8ExternalInput)
    port         = ByteField(19, enum=M8ExternalPort)
    channel      = ByteField(20)
    bank         = ByteField(21, default=0x7F)
    program      = ByteField(22, default=0x7F)

    cca_num      = ByteField(23, default=0x7F)
    cca_val      = ByteField(24, default=0x7F)
    ccb_num      = ByteField(25, default=0x7F)
    ccb_val      = ByteField(26, default=0x7F)
    ccc_num      = ByteField(27, default=0x7F)
    ccc_val      = ByteField(28, default=0x7F)
    ccd_num      = ByteField(29, default=0x7F)
    ccd_val      = ByteField(30, default=0x7F)

    filter_type  = ByteField(31, enum=M8FilterType)
    cutoff       = ByteField(32, default=0xFF)
    resonance    = ByteField(33)

    amp          = ByteField(34)
    limit        = ByteField(35, enum=M8LimiterType)
    pan          = ByteField(36, default=0x80)
    dry          = ByteField(37, default=0xC0)
    chorus_send  = ByteField(38)
    delay_send   = ByteField(39)
    reverb_send  = ByteField(40)
