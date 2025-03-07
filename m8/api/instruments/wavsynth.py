# m8/api/instruments/wavsynth.py
from m8.api.instruments import M8InstrumentBase

# m8/api/instruments/wavsynth_params.py
from m8.api.instruments.params import M8ParamsBase, M8ParamType

class M8WavSynthParams(M8ParamsBase):
    """Class to handle WavSynth-specific parameters."""
    
    _param_defs = [
        ("shape", 0x0, M8ParamType.UINT8),
        ("size", 0x80, M8ParamType.UINT8),
        ("mult", 0x80, M8ParamType.UINT8),
        ("warp", 0x0, M8ParamType.UINT8),
        ("scan", 0x0, M8ParamType.UINT8)
    ]
    
    def __init__(self, offset, **kwargs):
        super().__init__(self._param_defs, offset, **kwargs)

class M8WavSynth(M8InstrumentBase):
    # Define synth-specific offsets
    SYNTH_OFFSET = 18
    FILTER_OFFSET = 23
    AMP_OFFSET = 26
    MIXER_OFFSET = 28
    MODULATORS_OFFSET = 63
    
    def __init__(self, **kwargs):
        # Set type before calling parent class init
        self.type = 0x00
        
        # Extract synth-specific parameters
        synth_kwargs = {k.split("_")[1]: v for k, v in kwargs.items() if k.startswith('synth_')}
        
        # Also handle direct synth parameter references
        for key in ['shape', 'size', 'mult', 'warp', 'scan']:
            if key in kwargs:
                synth_kwargs[key] = kwargs[key]
        
        # Create synth parameter object with extracted kwargs
        self.synth = M8WavSynthParams(offset=self.SYNTH_OFFSET, **synth_kwargs)
        
        # Call parent constructor to finish setup
        super().__init__(**kwargs)
    
    def _read_specific_parameters(self, data, offset):
        """Read WavSynth-specific parameters"""
        self.synth = M8WavSynthParams.read(data, offset=offset)
    
    def _write_specific_parameters(self):
        """Write WavSynth-specific parameters"""
        return self.synth.write()
        
    def is_empty(self):
        """Check if the WavSynth instrument is empty"""
        return (self.name.strip() == "" and 
                self.volume == 0x0 and 
                self.synth.shape == 0x0)
