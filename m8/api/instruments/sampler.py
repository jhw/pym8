# m8/api/instruments/sampler.py
from m8.api.instruments import M8InstrumentBase, M8ParamsBase, M8ParamType

class M8SamplerParams(M8ParamsBase):
    """Class to handle Sampler parameters including synth parameters"""
    
    _param_defs = [
        # Synth section parameters
        ("play_mode", 0x0, M8ParamType.UINT8, 18, 19),
        ("slice", 0x0, M8ParamType.UINT8, 19, 20),
        ("start", 0x0, M8ParamType.UINT8, 20, 21),
        ("loop_start", 0x0, M8ParamType.UINT8, 21, 22),
        ("length", 0xFF, M8ParamType.UINT8, 22, 23),
        ("degrade", 0x0, M8ParamType.UINT8, 23, 24),
        
        # Filter section parameters
        ("filter", 0x0, M8ParamType.UINT8, 24, 25),
        ("cutoff", 0xFF, M8ParamType.UINT8, 25, 26),
        ("res", 0x0, M8ParamType.UINT8, 26, 27),
        
        # Amp section parameters
        ("amp", 0x0, M8ParamType.UINT8, 27, 28),
        ("limit", 0x0, M8ParamType.UINT8, 28, 29),
        
        # Mixer section parameters
        ("pan", 0x80, M8ParamType.UINT8, 29, 30),
        ("dry", 0xC0, M8ParamType.UINT8, 30, 31),
        ("chorus", 0x0, M8ParamType.UINT8, 31, 32),
        ("delay", 0x0, M8ParamType.UINT8, 32, 33),
        ("reverb", 0x0, M8ParamType.UINT8, 33, 34),
        
        # Sample path at offset 0x57 with length 128
        ("sample_path", "", M8ParamType.STRING, 0x57, 0x57 + 128)
    ]
    
    def __init__(self, offset=None, **kwargs):
        super().__init__(self._param_defs, offset, **kwargs)

class M8Sampler(M8InstrumentBase):
    # Different modulator offset from WavSynth and MacroSynth
    MODULATORS_OFFSET = 29
    
    def __init__(self, **kwargs):
        # Set type before calling parent class init
        self.type = 0x02
        
        # Create synth parameter object
        self.synth = M8SamplerParams()
        
        # Gather all parameters that match parameters in the synth object
        synth_kwargs = {}
        for key in kwargs:
            if hasattr(self.synth, key):
                synth_kwargs[key] = kwargs[key]
        
        # Apply the parameters to the synth object
        for key, value in synth_kwargs.items():
            setattr(self.synth, key, value)
        
        # Call parent constructor to finish setup
        super().__init__(**kwargs)
    
    def _read_specific_parameters(self, data, offset):
        """Read Sampler-specific parameters"""
        self.synth = M8SamplerParams.read(data)
    
    def is_empty(self):
        """Check if the Sampler instrument is empty"""
        return (self.name.strip() == "" and 
                self.volume == 0x0 and 
                self.synth.sample_path == "")
