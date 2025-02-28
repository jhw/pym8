from m8.api.instruments import M8InstrumentBase, M8MixerParams, M8FilterParams, M8AmpParams, M8ParamsBase

class M8MacroSynthParams(M8ParamsBase):
    """Class to handle MacroSynth-specific parameters."""
    
    _param_defs = [
        ("shape", 0x0),
        ("timbre", 0x80),
        ("color", 0x80),
        ("degrade", 0x0),
        ("redux", 0x0)
    ]
    
    def __init__(self, offset=19, **kwargs):
        super().__init__(self._param_defs, offset, **kwargs)

class M8MacroSynth(M8InstrumentBase):
    def __init__(self, **kwargs):
        # Set type before calling parent class init
        self.type = 0x01
    
        # Extract prefixed parameters for each group
        filter_kwargs = {k[7:]: v for k, v in kwargs.items() if k.startswith('filter_')}
        amp_kwargs = {k[4:]: v for k, v in kwargs.items() if k.startswith('amp_')}
        mixer_kwargs = {k[6:]: v for k, v in kwargs.items() if k.startswith('mixer_')}
        synth_kwargs = {k[6:]: v for k, v in kwargs.items() if k.startswith('synth_')}
    
        # Also handle direct synth parameter references (like 'shape' instead of 'synth_shape')
        for key in ['shape', 'timbre', 'color', 'degrade', 'redux']:
            if key in kwargs:
                synth_kwargs[key] = kwargs[key]
    
        # Create parameter group objects with extracted kwargs
        self.synth = M8MacroSynthParams(offset=19, **synth_kwargs)
        self.filter = M8FilterParams(offset=24, **filter_kwargs)
        self.amp = M8AmpParams(offset=27, **amp_kwargs)
        self.mixer = M8MixerParams(offset=29, **mixer_kwargs)
    
        # Call parent constructor to finish setup
        super().__init__(**kwargs)
    
    def _read_parameters(self, data):
        """Read MacroSynth parameters from binary data"""
        # Read common parameters first
        next_offset = self._read_common_parameters(data)
        
        # Read synth, filter, amp, and mixer parameters
        self.synth = M8MacroSynthParams.read(data, offset=next_offset)  # next_offset should be 19
        self.filter = M8FilterParams.read(data, offset=24)
        self.amp = M8AmpParams.read(data, offset=27)
        self.mixer = M8MixerParams.read(data, offset=29)
    
    def is_empty(self):
        """Check if the MacroSynth instrument is empty"""
        return (self.name.strip() == "" and 
                self.volume == 0x0 and 
                self.synth.shape == 0x0)

