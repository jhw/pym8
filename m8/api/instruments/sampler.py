# m8/api/instruments/sampler.py
from m8.api.instruments import M8InstrumentBase, M8ParamsBase, M8ParamType

class M8SamplerParams(M8ParamsBase):
    """Sampler parameters including playback, filtering, amp, and mixer settings."""
    
    _param_defs = {
        # Synth section parameters
        "play_mode": {"offset": 18, "size": 1, "type": "UINT8", "default": 0x00},
        "slice": {"offset": 19, "size": 1, "type": "UINT8", "default": 0x00},
        "start": {"offset": 20, "size": 1, "type": "UINT8", "default": 0x00},
        "loop_start": {"offset": 21, "size": 1, "type": "UINT8", "default": 0x00},
        "length": {"offset": 22, "size": 1, "type": "UINT8", "default": 0xFF},
        "degrade": {"offset": 23, "size": 1, "type": "UINT8", "default": 0x00},
        
        # Filter section parameters
        "filter": {"offset": 24, "size": 1, "type": "UINT8", "default": 0x00},
        "cutoff": {"offset": 25, "size": 1, "type": "UINT8", "default": 0xFF},
        "res": {"offset": 26, "size": 1, "type": "UINT8", "default": 0x00},
        
        # Amp section parameters
        "amp": {"offset": 27, "size": 1, "type": "UINT8", "default": 0x00},
        "limit": {"offset": 28, "size": 1, "type": "UINT8", "default": 0x00},
        
        # Mixer section parameters
        "pan": {"offset": 29, "size": 1, "type": "UINT8", "default": 0x80},
        "dry": {"offset": 30, "size": 1, "type": "UINT8", "default": 0xC0},
        "chorus": {"offset": 31, "size": 1, "type": "UINT8", "default": 0x00},
        "delay": {"offset": 32, "size": 1, "type": "UINT8", "default": 0x00},
        "reverb": {"offset": 33, "size": 1, "type": "UINT8", "default": 0x00},
        
        # Sample path at offset 0x57 with length 128
        "sample_path": {"offset": 0x57, "size": 128, "type": "STRING", "default": ""}
    }
    
    def __init__(self, **kwargs):
        """Initialize Sampler parameters."""
        super().__init__(self._param_defs, **kwargs)

class M8Sampler(M8InstrumentBase):
    """Sampler instrument implementation for the M8 tracker."""
    
    # Offset for modulator data in the binary structure
    MODULATORS_OFFSET = 63
    
    def __init__(self, **kwargs):
        """Initialize a Sampler instrument."""
        # Set type before calling parent class init
        self.type = 0x02  # Type ID for Sampler instruments
        
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
        """Read Sampler-specific parameters from binary data."""
        self.synth = M8SamplerParams.read(data)
    
    def _write_specific_parameters(self):
        """Write Sampler-specific parameters to binary format."""
        return self.synth.write()
    
    def is_empty(self):
        """Check if the Sampler instrument is empty/initialized to defaults."""
        return (self.name.strip() == "" and 
                self.volume == 0x0 and 
                self.synth.sample_path == "")