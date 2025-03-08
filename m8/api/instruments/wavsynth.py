# m8/api/instruments/wavsynth.py
from m8.api.instruments import M8InstrumentBase, M8ParamsBase, M8ParamType

class M8WavSynthParams(M8ParamsBase):
    """Class to handle all WavSynth parameters including synth, filter, amp, and mixer settings."""
    
    _param_defs = [
        # Synth section parameters
        ("shape", 0x0, M8ParamType.UINT8, 18, 19),
        ("size", 0x80, M8ParamType.UINT8, 19, 20),
        ("mult", 0x80, M8ParamType.UINT8, 20, 21),
        ("warp", 0x0, M8ParamType.UINT8, 21, 22),
        ("scan", 0x0, M8ParamType.UINT8, 22, 23),
        
        # Filter section parameters
        ("filter", 0x0, M8ParamType.UINT8, 23, 24),  # renamed from filter_type
        ("cutoff", 0xFF, M8ParamType.UINT8, 24, 25),
        ("res", 0x0, M8ParamType.UINT8, 25, 26),    # renamed from resonance
        
        # Amp section parameters
        ("amp", 0x0, M8ParamType.UINT8, 26, 27),     # renamed from amp_level
        ("limit", 0x0, M8ParamType.UINT8, 27, 28),
        
        # Mixer section parameters
        ("pan", 0x80, M8ParamType.UINT8, 28, 29),
        ("dry", 0xC0, M8ParamType.UINT8, 29, 30),
        ("chorus", 0x0, M8ParamType.UINT8, 30, 31),
        ("delay", 0x0, M8ParamType.UINT8, 31, 32),
        ("reverb", 0x0, M8ParamType.UINT8, 32, 33)
    ]
    
    def __init__(self, offset=None, **kwargs):
        super().__init__(self._param_defs, offset, **kwargs)

class M8WavSynth(M8InstrumentBase):
    # Only keep the modulators offset
    MODULATORS_OFFSET = 63
    
    def __init__(self, **kwargs):
        # Set type before calling parent class init
        # Using hex to ensure it's stored as 0x00, not 0
        self.type = 0x00
        # Type is set to 0x00 for WavSynth
        
        # Extract all parameters that match synth parameters
        synth_kwargs = {}
        
        # Create synth parameter object with extracted kwargs
        self.synth = M8WavSynthParams()
        
        # Gather all parameters that match parameters in the synth object
        for key in kwargs:
            if hasattr(self.synth, key):
                synth_kwargs[key] = kwargs[key]
        
        # Apply the parameters to the synth object
        for key, value in synth_kwargs.items():
            setattr(self.synth, key, value)
        
        # Call parent constructor to finish setup
        super().__init__(**kwargs)
    
    def _read_specific_parameters(self, data, offset):
        """Read WavSynth-specific parameters"""
        self.synth = M8WavSynthParams.read(data)
    
    def _write_specific_parameters(self):
        """Write WavSynth-specific parameters"""
        return self.synth.write()
        
    def is_empty(self):
        """Check if the WavSynth instrument is empty"""
        return (self.name.strip() == "" and 
                self.volume == 0x0 and 
                self.synth.shape == 0x0)
