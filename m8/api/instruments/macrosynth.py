# m8/api/instruments/macrosynth.py
from m8.api.instruments import M8InstrumentBase, M8ParamsBase, M8ParamType
from m8.config import load_format_config, get_instrument_modulators_offset

class M8MacroSynthParams(M8ParamsBase):
    """MacroSynth parameters including synth, filter, amp, and mixer settings."""
    
    # Load parameter definitions from YAML config
    _param_defs = load_format_config()["instruments"]["macrosynth"]["params"]
    
    def __init__(self, **kwargs):
        """Initialize MacroSynth parameters."""
        super().__init__(self._param_defs, **kwargs)

class M8MacroSynth(M8InstrumentBase):
    """MacroSynth instrument implementation for the M8 tracker."""
    
    # Offset for modulator data in the binary structure - from config
    MODULATORS_OFFSET = get_instrument_modulators_offset("macrosynth")
    
    def __init__(self, **kwargs):
        """Initialize a MacroSynth instrument."""
        # Set type from config before calling parent class init
        from m8.config import get_instrument_type_id
        self.type = get_instrument_type_id("macrosynth")
        
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