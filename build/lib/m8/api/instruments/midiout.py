# m8/api/instruments/midiout.py
"""M8 MIDIOut instrument (type 3) — pure MIDI output to external gear.

Distinct from M8External (type 6, which is for audio-input routing). MIDIOut
is the right choice for sequencing external hardware/software synths over
MIDI: it exposes 10 CC slots (CCA-CCJ), no filter/amp section, and a
port enum including INTERNAL for routing to the M8's own internal mixer.

Binary layout follows m8-file-parser's MIDIOut::from_reader: name, transpose,
table_tick, port, channel, bank, program, 3 reserved bytes, then 10 (num,
value) CC pairs. Modulators sit at the standard offset (63) within the block.
"""

from enum import IntEnum

from m8.api.fields import ByteField
from m8.api.instrument import M8Instrument, M8InstrumentType


class M8MIDIPort(IntEnum):
    """MIDIOut port. Note INTERNAL routes to the M8's own mixer (no external send)."""
    MIDI_USB = 0x00
    MIDI = 0x01
    USB = 0x02
    INTERNAL = 0x03


class M8MIDIOutModDest(IntEnum):
    """MIDIOut modulator destinations (15 entries, includes CCE-CCJ)."""
    OFF = 0x00
    CCA = 0x01
    CCB = 0x02
    CCC = 0x03
    CCD = 0x04
    CCE = 0x05
    CCF = 0x06
    CCG = 0x07
    CCH = 0x08
    CCI = 0x09
    CCJ = 0x0A
    MOD_AMT = 0x0B
    MOD_RATE = 0x0C
    MOD_BOTH = 0x0D
    MOD_BINV = 0x0E


class M8MIDIOut(M8Instrument):
    """MIDI-output instrument with 10 customizable CC slots (type 3)."""

    TYPE_ID = M8InstrumentType.MIDIOUT
    MOD_DEST_ENUM_CLASS = M8MIDIOutModDest

    transpose   = ByteField(13)
    table_tick  = ByteField(14)

    port        = ByteField(15, enum=M8MIDIPort)
    channel     = ByteField(16)
    bank        = ByteField(17, default=0x7F)
    program     = ByteField(18, default=0x7F)
    # bytes 19-21 are reserved/padding in the binary format

    cca_num     = ByteField(22, default=0x7F)
    cca_val     = ByteField(23, default=0x7F)
    ccb_num     = ByteField(24, default=0x7F)
    ccb_val     = ByteField(25, default=0x7F)
    ccc_num     = ByteField(26, default=0x7F)
    ccc_val     = ByteField(27, default=0x7F)
    ccd_num     = ByteField(28, default=0x7F)
    ccd_val     = ByteField(29, default=0x7F)
    cce_num     = ByteField(30, default=0x7F)
    cce_val     = ByteField(31, default=0x7F)
    ccf_num     = ByteField(32, default=0x7F)
    ccf_val     = ByteField(33, default=0x7F)
    ccg_num     = ByteField(34, default=0x7F)
    ccg_val     = ByteField(35, default=0x7F)
    cch_num     = ByteField(36, default=0x7F)
    cch_val     = ByteField(37, default=0x7F)
    cci_num     = ByteField(38, default=0x7F)
    cci_val     = ByteField(39, default=0x7F)
    ccj_num     = ByteField(40, default=0x7F)
    ccj_val     = ByteField(41, default=0x7F)
