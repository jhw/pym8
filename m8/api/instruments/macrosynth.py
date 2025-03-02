# m8/api/instruments/macrosynth.py
from m8.api.instruments import M8InstrumentBase
from m8.api.instruments.params import M8ParamsBase

class M8MacroSynthParams(M8ParamsBase):
    """Class to handle MacroSynth-specific parameters."""
    
    _param_defs = [
        ("shape", 0x0),
        ("timbre", 0x80),
        ("color", 0x80),
        ("degrade", 0x0),
        ("redux", 0x0)
    ]
    
    def __init__(self, offset=None, **kwargs):
        # If no offset provided, use parent class's SYNTH_OFFSET
        if offset is None:
            offset = M8InstrumentBase.SYNTH_OFFSET
        super().__init__(self._param_defs, offset, **kwargs)

class M8MacroSynth(M8InstrumentBase):
    # No need to override offsets as we're using the parent class offsets
    
    def __init__(self, **kwargs):
        # Set type before calling parent class init
        self.type = 0x01
        
        # Extract synth-specific parameters
        synth_kwargs = {k[6:]: v for k, v in kwargs.items() if k.startswith('synth_')}
        
        # Also handle direct synth parameter references (like 'shape' instead of 'synth_shape')
        for key in ['shape', 'timbre', 'color', 'degrade', 'redux']:
            if key in kwargs:
                synth_kwargs[key] = kwargs[key]
        
        # Create synth parameter object with extracted kwargs
        # Use the class constant SYNTH_OFFSET from the parent class
        self.synth = M8MacroSynthParams(**synth_kwargs)
        
        # Call parent constructor to finish setup (will handle filter/amp/mixer)
        super().__init__(**kwargs)
    
    def _read_specific_parameters(self, data, offset):
        """Read MacroSynth-specific parameters"""
        self.synth = M8MacroSynthParams.read(data, offset=offset)
        
    def is_empty(self):
        """Check if the MacroSynth instrument is empty"""
        return (self.name.strip() == "" and 
                self.volume == 0x0 and 
                self.synth.shape == 0x0)
