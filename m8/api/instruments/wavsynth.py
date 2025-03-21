# m8/api/instruments/wavsynth.py
from m8.api.instruments import M8InstrumentBase, M8ParamsBase, M8ParamType
from m8.config import load_format_config, get_param_type_enum

# Load wavsynth configuration
config = load_format_config()["instruments"]["wavsynth"]["params"]

class M8WavSynthParams(M8ParamsBase):
    """WavSynth parameters including synth, filter, amp, and mixer settings."""
    
    # Build parameter definitions from configuration
    _param_defs = []
    
    # Dynamically build parameter definitions from configuration
    for param_name, param_data in config.items():
        # Get parameter type (enum value or use UINT8 as default)
        param_type = M8ParamType.UINT8
        if "type" in param_data:
            type_enum_value = get_param_type_enum(param_data["type"])
            param_type = M8ParamType(type_enum_value)
            
        default_value = param_data.get("default", 0x0)
        offset = param_data["offset"]
        size = param_data["size"]
        
        # Add parameter definition
        _param_defs.append(
            (param_name, default_value, param_type, offset, offset + size)
        )
    
    def __init__(self, **kwargs):
        """Initialize WavSynth parameters."""
        super().__init__(self._param_defs, **kwargs)

class M8WavSynth(M8InstrumentBase):
    """WavSynth instrument implementation for the M8 tracker."""
    
    # Offset for modulator data in the binary structure - from config
    MODULATORS_OFFSET = load_format_config()["instruments"]["wavsynth"]["modulators_offset"]
    
    def __init__(self, **kwargs):
        """Initialize a WavSynth instrument."""
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
        """Read WavSynth-specific parameters from binary data."""
        self.synth = M8WavSynthParams.read(data)
    
    def _write_specific_parameters(self):
        """Write WavSynth-specific parameters to binary format."""
        return self.synth.write()
        
    def is_empty(self):
        """Check if the WavSynth instrument is empty/initialized to defaults."""
        return (self.name.strip() == "" and 
                self.volume == 0x0 and 
                self.synth.shape == 0x0)
