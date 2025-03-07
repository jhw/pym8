# m8/api/instruments/macrosynth.py
from m8.api.instruments import M8InstrumentBase
from m8.api.instruments.params import M8ParamsBase, M8ParamType

class M8MacroSynthParams(M8ParamsBase):
    """Class to handle MacroSynth-specific parameters."""
    
    _param_defs = [
        ("shape", 0x0, M8ParamType.UINT8),
        ("timbre", 0x80, M8ParamType.UINT8),
        ("color", 0x80, M8ParamType.UINT8),
        ("degrade", 0x0, M8ParamType.UINT8),
        ("redux", 0x0, M8ParamType.UINT8)
    ]
    
    def __init__(self, offset, **kwargs):
        super().__init__(self._param_defs, offset, **kwargs)

class M8MacroSynth(M8InstrumentBase):
    # Define synth-specific offsets
    SYNTH_OFFSET = 18
    FILTER_OFFSET = 23
    AMP_OFFSET = 26
    MIXER_OFFSET = 28
    MODULATORS_OFFSET = 63
    
    def __init__(self, **kwargs):
        # Set type before calling parent class init
        self.type = 0x01
        
        # Extract synth-specific parameters - no conditional checks
        synth_kwargs = {k.split("_")[1]: v for k, v in kwargs.items() if k.startswith('synth_')}
        
        # Also handle direct synth parameter references (like 'shape' instead of 'synth_shape')
        for key in ['shape', 'timbre', 'color', 'degrade', 'redux']:
            if key in kwargs:
                synth_kwargs[key] = kwargs[key]
        
        # Create synth parameter object with extracted kwargs
        # Use the class-specific SYNTH_OFFSET
        self.synth = M8MacroSynthParams(offset=self.SYNTH_OFFSET, **synth_kwargs)
        
        # Call parent constructor to finish setup
        super().__init__(**kwargs)
    
    def _read_specific_parameters(self, data, offset):
        """Read MacroSynth-specific parameters"""
        self.synth = M8MacroSynthParams.read(data, offset=offset)
        
    def is_empty(self):
        """Check if the MacroSynth instrument is empty"""
        return (self.name.strip() == "" and 
                self.volume == 0x0 and 
                self.synth.shape == 0x0)
        
