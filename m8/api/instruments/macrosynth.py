# m8/api/instruments/macrosynth.py
from m8.api.instruments import M8InstrumentBase, M8ParamsBase, M8ParamType

class M8MacroSynthParams(M8ParamsBase):
    """MacroSynth parameters including synth, filter, amp, and mixer settings."""
    
    _param_defs = {
        # Synth section parameters
        "shape": {"offset": 18, "size": 1, "type": "UINT8", "default": 0x00},
        "timbre": {"offset": 19, "size": 1, "type": "UINT8", "default": 0x80},
        "color": {"offset": 20, "size": 1, "type": "UINT8", "default": 0x80},
        "degrade": {"offset": 21, "size": 1, "type": "UINT8", "default": 0x00},
        "redux": {"offset": 22, "size": 1, "type": "UINT8", "default": 0x00},
        
        # Filter section parameters
        "filter": {"offset": 23, "size": 1, "type": "UINT8", "default": 0x00},
        "cutoff": {"offset": 24, "size": 1, "type": "UINT8", "default": 0xFF},
        "res": {"offset": 25, "size": 1, "type": "UINT8", "default": 0x00},
        
        # Amp section parameters
        "amp": {"offset": 26, "size": 1, "type": "UINT8", "default": 0x00},
        "limit": {"offset": 27, "size": 1, "type": "UINT8", "default": 0x00},
        
        # Mixer section parameters
        "pan": {"offset": 28, "size": 1, "type": "UINT8", "default": 0x80},
        "dry": {"offset": 29, "size": 1, "type": "UINT8", "default": 0xC0},
        "chorus": {"offset": 30, "size": 1, "type": "UINT8", "default": 0x00},
        "delay": {"offset": 31, "size": 1, "type": "UINT8", "default": 0x00},
        "reverb": {"offset": 32, "size": 1, "type": "UINT8", "default": 0x00}
    }
    
    def __init__(self, **kwargs):
        """Initialize MacroSynth parameters."""
        super().__init__(self._param_defs, **kwargs)

class M8MacroSynth(M8InstrumentBase):
    """MacroSynth instrument implementation for the M8 tracker."""
    
    # Offset for modulator data in the binary structure
    MODULATORS_OFFSET = 63
    
    def __init__(self, **kwargs):
        """Initialize a MacroSynth instrument."""
        # Set type before calling parent class init
        # Using hex to ensure it's stored as 0x01, not 1
        self.type = 0x01
        # Type is set to 0x01 for MacroSynth
        
        # Extract all parameters that match synth parameters
        synth_kwargs = {}
        
        # Create synth parameter object with extracted kwargs
        self.synth = M8MacroSynthParams()
        
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
        """Read MacroSynth-specific parameters from binary data."""
        self.synth = M8MacroSynthParams.read(data)
    
    def _write_specific_parameters(self):
        """Write MacroSynth-specific parameters to binary format."""
        return self.synth.write()
        
    def is_empty(self):
        """Check if the MacroSynth instrument is empty/initialized to defaults."""
        return (self.name.strip() == "" and 
                self.volume == 0x0 and 
                self.synth.shape == 0x0)