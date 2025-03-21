# m8/api/instruments/sampler.py
from m8.api.instruments import M8InstrumentBase, M8ParamsBase, M8ParamType
from m8.config import load_format_config, get_instrument_modulators_offset, get_instrument_type_id

class M8SamplerParams(M8ParamsBase):
    """Sampler parameters including playback, filtering, amp, and mixer settings."""
    
    # Load parameter definitions from YAML config
    _param_defs = load_format_config()["instruments"]["sampler"]["params"]
    # Add sample_path parameter from top level sampler config
    _param_defs["sample_path"] = load_format_config()["instruments"]["sampler"]["sample_path"]
    
    def __init__(self, **kwargs):
        """Initialize Sampler parameters."""
        super().__init__(self._param_defs, **kwargs)

class M8Sampler(M8InstrumentBase):
    """Sampler instrument implementation for the M8 tracker."""
    
    # Offset for modulator data in the binary structure - from config
    MODULATORS_OFFSET = get_instrument_modulators_offset("sampler")
    
    def __init__(self, **kwargs):
        """Initialize a Sampler instrument."""
        # Set type from config before calling parent class init
        self.type = get_instrument_type_id("sampler")
        
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