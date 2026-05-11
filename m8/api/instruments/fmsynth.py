# m8/api/instruments/fmsynth.py
"""M8 FM Synth instrument - 4-operator FM synthesizer."""

from enum import IntEnum

from m8.api.fields import ByteField
from m8.api.instrument import (
    M8FilterType,
    M8Instrument,
    M8InstrumentType,
    M8LimiterType,
)


class M8FMAlgo(IntEnum):
    """FM synthesis algorithms - operator routing configurations."""
    A_B_C_D = 0
    AB_C_D = 1
    AB_C_D_ALT = 2
    A_BC_D = 3
    ABC_D = 4
    A_B_C_D_PARALLEL = 5
    A_B_C_A_B_D = 6
    A_B_C_D_TWO_PAIR = 7
    A_B_A_C_A_D = 8
    A_B_A_C_D = 9
    A_B_C_D_THREE = 10
    A_PLUS_B_PLUS_C_PLUS_D = 11


class M8FMWave(IntEnum):
    """FM operator waveform shapes."""
    SIN = 0
    SW2 = 1
    SW3 = 2
    SW4 = 3
    SW5 = 4
    SW6 = 5
    TRI = 6
    SAW = 7
    SQR = 8
    PUL = 9
    IMP = 10
    NOI = 11
    NLP = 12
    NHP = 13
    NBP = 14
    CLK = 15
    W09 = 16
    W0A = 17
    W0B = 18
    W0C = 19
    W0D = 20
    W0E = 21
    W0F = 22
    W10 = 23
    W11 = 24
    W12 = 25
    W13 = 26
    W14 = 27
    W15 = 28
    W16 = 29
    W17 = 30
    W18 = 31
    W19 = 32
    W1A = 33
    W1B = 34
    W1C = 35
    W1D = 36
    W1E = 37
    W1F = 38
    W20 = 39
    W21 = 40
    W22 = 41
    W23 = 42
    W24 = 43
    W25 = 44
    W26 = 45
    W27 = 46
    W28 = 47
    W29 = 48
    W2A = 49
    W2B = 50
    W2C = 51
    W2D = 52
    W2E = 53
    W2F = 54
    W30 = 55
    W31 = 56
    W32 = 57
    W33 = 58
    W34 = 59
    W35 = 60
    W36 = 61
    W37 = 62
    W38 = 63
    W39 = 64
    W3A = 65
    W3B = 66
    W3C = 67
    W3D = 68
    W3E = 69
    W3F = 70
    W40 = 71
    W41 = 72
    W42 = 73
    W43 = 74
    W44 = 75
    W45 = 76


class M8FMSynthModDest(IntEnum):
    """FM synth modulator destinations."""
    OFF = 0x00
    VOLUME = 0x01
    PITCH = 0x02
    MOD1 = 0x03
    MOD2 = 0x04
    MOD3 = 0x05
    MOD4 = 0x06
    CUTOFF = 0x07
    RES = 0x08
    AMP = 0x09
    PAN = 0x0A
    MOD_AMT = 0x0B
    MOD_RATE = 0x0C
    MOD_BOTH = 0x0D
    MOD_BINV = 0x0E


class M8FMOperatorModDest(IntEnum):
    """FM operator modulation routing — {modulator}/{param} pairs."""
    OFF = 0x00
    MOD1_LEV = 0x01
    MOD1_RAT = 0x02
    MOD1_PIT = 0x03
    MOD1_FBK = 0x04
    MOD2_LEV = 0x05
    MOD2_RAT = 0x06
    MOD2_PIT = 0x07
    MOD2_FBK = 0x08
    MOD3_LEV = 0x09
    MOD3_RAT = 0x0A
    MOD3_PIT = 0x0B
    MOD3_FBK = 0x0C
    MOD4_LEV = 0x0D
    MOD4_RAT = 0x0E
    MOD4_PIT = 0x0F
    MOD4_FBK = 0x10


class M8FMSynth(M8Instrument):
    """4-operator FM synthesizer."""

    TYPE_ID = M8InstrumentType.FMSYNTH
    MOD_DEST_ENUM_CLASS = M8FMSynthModDest

    transpose       = ByteField(13)
    table_tick      = ByteField(14)
    volume          = ByteField(15)
    pitch           = ByteField(16)
    fine_tune       = ByteField(17, default=0x80)

    algo            = ByteField(18, enum=M8FMAlgo)

    op_a_shape      = ByteField(19, enum=M8FMWave)
    op_b_shape      = ByteField(20, enum=M8FMWave)
    op_c_shape      = ByteField(21, enum=M8FMWave)
    op_d_shape      = ByteField(22, enum=M8FMWave)

    op_a_ratio      = ByteField(23)
    op_a_ratio_fine = ByteField(24)
    op_b_ratio      = ByteField(25)
    op_b_ratio_fine = ByteField(26)
    op_c_ratio      = ByteField(27)
    op_c_ratio_fine = ByteField(28)
    op_d_ratio      = ByteField(29)
    op_d_ratio_fine = ByteField(30)

    op_a_level      = ByteField(31)
    op_a_feedback   = ByteField(32)
    op_b_level      = ByteField(33)
    op_b_feedback   = ByteField(34)
    op_c_level      = ByteField(35)
    op_c_feedback   = ByteField(36)
    op_d_level      = ByteField(37)
    op_d_feedback   = ByteField(38)

    op_a_mod_a      = ByteField(39, enum=M8FMOperatorModDest)
    op_b_mod_a      = ByteField(40, enum=M8FMOperatorModDest)
    op_c_mod_a      = ByteField(41, enum=M8FMOperatorModDest)
    op_d_mod_a      = ByteField(42, enum=M8FMOperatorModDest)
    op_a_mod_b      = ByteField(43, enum=M8FMOperatorModDest)
    op_b_mod_b      = ByteField(44, enum=M8FMOperatorModDest)
    op_c_mod_b      = ByteField(45, enum=M8FMOperatorModDest)
    op_d_mod_b      = ByteField(46, enum=M8FMOperatorModDest)

    mod1_value      = ByteField(47)
    mod2_value      = ByteField(48)
    mod3_value      = ByteField(49)
    mod4_value      = ByteField(50)

    filter_type     = ByteField(51, enum=M8FilterType)
    cutoff          = ByteField(52, default=0xFF)
    resonance       = ByteField(53)

    amp             = ByteField(54)
    limit           = ByteField(55, enum=M8LimiterType)
    pan             = ByteField(56, default=0x80)
    dry             = ByteField(57, default=0xC0)
    chorus_send     = ByteField(58)
    delay_send      = ByteField(59)
    reverb_send     = ByteField(60)
