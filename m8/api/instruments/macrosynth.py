from m8.api import split_byte, join_nibbles
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
        
        # Create parameter group objects with default values
        self.synth = M8MacroSynthParams(offset=19)
        self.filter = M8FilterParams(offset=24)
        self.amp = M8AmpParams(offset=27)
        self.mixer = M8MixerParams(offset=29)
        
        # Handle synth-specific parameters directly
        for key in ['shape', 'timbre', 'color', 'degrade', 'redux']:
            if key in kwargs:
                setattr(self.synth, key, kwargs[key])
        
        # Now apply prefixed parameters to the appropriate groupings
        filter_params = M8FilterParams.from_prefixed_dict(kwargs, prefix="filter_", offset=24)
        amp_params = M8AmpParams.from_prefixed_dict(kwargs, prefix="amp_", offset=27)
        mixer_params = M8MixerParams.from_prefixed_dict(kwargs, prefix="mixer_", offset=29)
        synth_params = M8MacroSynthParams.from_prefixed_dict(kwargs, prefix="synth_", offset=19)
        
        # Assign the parameter groups
        if any(k.startswith('filter_') for k in kwargs):
            self.filter = filter_params
        if any(k.startswith('amp_') for k in kwargs):
            self.amp = amp_params
        if any(k.startswith('mixer_') for k in kwargs):
            self.mixer = mixer_params
            
        # Only update synth attributes that weren't directly set
        for key in ['shape', 'timbre', 'color', 'degrade', 'redux']:
            if key not in kwargs and any(k.startswith('synth_') for k in kwargs):
                setattr(self.synth, key, getattr(synth_params, key))
            
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

    def _write_parameters(self):
        """Write MacroSynth parameters to binary data"""
        # Write common parameters first
        buffer = bytearray(self._write_common_parameters())
        
        # Add synth, filter, amp, and mixer parameters
        buffer.extend(self.synth.write())
        buffer.extend(self.filter.write())
        buffer.extend(self.amp.write())
        buffer.extend(self.mixer.write())
        
        return bytes(buffer)
    
    def is_empty(self):
        """Check if the MacroSynth instrument is empty"""
        return (self.name.strip() == "" and 
                self.volume == 0x0 and 
                self.synth.shape == 0x0)

    def as_dict(self):
        """Convert MacroSynth to dictionary for serialization"""
        # Use parent implementation, which now correctly handles
        # nested objects with as_dict methods
        return super().as_dict()
