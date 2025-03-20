# m8/api/instruments/macrosynth.py
from m8.api.instruments import M8InstrumentBase, M8ParamsBase, M8ParamType

class M8MacroSynthParams(M8ParamsBase):
    """MacroSynth parameters including synth, filter, amp, and mixer settings."""
    
    _param_defs = [
        # Synth section parameters
        ("shape", 0x0, M8ParamType.UINT8, 18, 19),     # Waveform shape (0-127)
        ("timbre", 0x80, M8ParamType.UINT8, 19, 20),   # Timbre control - default 0x80 (centered)
        ("color", 0x80, M8ParamType.UINT8, 20, 21),    # Color control - default 0x80 (centered)
        ("degrade", 0x0, M8ParamType.UINT8, 21, 22),   # Bit degradation amount
        ("redux", 0x0, M8ParamType.UINT8, 22, 23),     # Sample rate reduction
        
        # Filter section parameters
        ("filter", 0x0, M8ParamType.UINT8, 23, 24),    # Filter type selection
        ("cutoff", 0xFF, M8ParamType.UINT8, 24, 25),   # Filter cutoff frequency - default 0xFF (fully open)
        ("res", 0x0, M8ParamType.UINT8, 25, 26),       # Filter resonance
        
        # Amp section parameters
        ("amp", 0x0, M8ParamType.UINT8, 26, 27),       # Amplifier drive amount
        ("limit", 0x0, M8ParamType.UINT8, 27, 28),     # Limiting amount
        
        # Mixer section parameters
        ("pan", 0x80, M8ParamType.UINT8, 28, 29),      # Stereo panning - default 0x80 (centered)
        ("dry", 0xC0, M8ParamType.UINT8, 29, 30),      # Dry signal level - default 0xC0 (75%)
        ("chorus", 0x0, M8ParamType.UINT8, 30, 31),    # Chorus send level
        ("delay", 0x0, M8ParamType.UINT8, 31, 32),     # Delay send level
        ("reverb", 0x0, M8ParamType.UINT8, 32, 33)     # Reverb send level
    ]
    
    def __init__(self, offset=None, **kwargs):
        """Initialize MacroSynth parameters."""
        super().__init__(self._param_defs, offset, **kwargs)

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
        
