from m8 import NULL, BLANK
from m8.core.object import m8_object_class
from m8.api.instruments import M8InstrumentBase

M8MacroSynthParams = m8_object_class(
    field_map=[
        ("type", 0x01, 0, 1, "UINT8"),
        ("name", " ", 1, 13, "STRING"),  
        ("transpose|eq", 0x41, 13, 14, "UINT4_2"),
        ("table_tick", 0x01, 14, 15, "UINT8"),
        ("volume", NULL, 15, 16, "UINT8"), 
        ("pitch", NULL, 16, 17, "UINT8"), 
        ("fine_tune", 0x80, 17, 18, "UINT8"),
        ("shape", NULL, 18, 19, "UINT8"),
        ("timbre", 0x80, 19, 20, "UINT8"),
        ("color", 0x80, 20, 21, "UINT8"),
        ("degrade", NULL, 21, 22, "UINT8"),
        ("redux", NULL, 22, 23, "UINT8"),
        ("filter_type", NULL, 23, 24, "UINT8"),
        ("filter_cutoff", BLANK, 24, 25, "UINT8"),
        ("filter_resonance", NULL, 25, 26, "UINT8"),
        ("amp_level", NULL, 26, 27, "UINT8"),
        ("amp_limit", NULL, 27, 28, "UINT8"),
        ("mixer_pan", 0x80, 28, 29, "UINT8"),
        ("mixer_dry", 0xC0, 29, 30, "UINT8"),
        ("mixer_chorus", NULL, 30, 31, "UINT8"),
        ("mixer_delay", NULL, 31, 32, "UINT8"),
        ("mixer_reverb", NULL, 32, 33, "UINT8")
    ]
)

class M8MacroSynth(M8InstrumentBase):
    def __init__(self, **kwargs):
        super().__init__(synth_params_class=M8MacroSynthParams, **kwargs)

    @classmethod
    def read(cls, data):
        return super().read(data, synth_params_class=M8MacroSynthParams)
