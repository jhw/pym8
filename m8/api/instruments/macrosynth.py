from m8.api import split_byte, join_nibbles
from m8.api.instruments import M8InstrumentBase, M8MixerParams, M8FilterParams, M8AmpParams

class M8MacroSynthParams:
    """Class to handle MacroSynth-specific parameters."""
    
    def __init__(self, offset=19, **kwargs):
        # Default parameter values
        self.shape = 0x0
        self.timbre = 0x80
        self.color = 0x80
        self.degrade = 0x0
        self.redux = 0x0
        
        # Store the offset where these parameters start in the binary data
        self.offset = offset
        
        # Apply any kwargs
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    @classmethod
    def read(cls, data, offset=19):
        """Read MacroSynth parameters from binary data starting at a specific offset"""
        instance = cls(offset)
        
        # Read values from appropriate offsets
        instance.shape = data[offset]
        instance.timbre = data[offset + 1]
        instance.color = data[offset + 2]
        instance.degrade = data[offset + 3]
        instance.redux = data[offset + 4]
        
        return instance
    
    def write(self):
        """Write MacroSynth parameters to binary data"""
        buffer = bytearray()
        buffer.append(self.shape)
        buffer.append(self.timbre)
        buffer.append(self.color)
        buffer.append(self.degrade)
        buffer.append(self.redux)
        return bytes(buffer)
    
    def clone(self):
        """Create a copy of this MacroSynth parameters object"""
        instance = self.__class__(self.offset)
        instance.shape = self.shape
        instance.timbre = self.timbre
        instance.color = self.color
        instance.degrade = self.degrade
        instance.redux = self.redux
        return instance
    
    def as_dict(self):
        """Convert MacroSynth parameters to dictionary for serialization"""
        return {
            "shape": self.shape,
            "timbre": self.timbre,
            "color": self.color,
            "degrade": self.degrade,
            "redux": self.redux
        }
    
    @classmethod
    def from_dict(cls, data, offset=19):
        """Create MacroSynth parameters from a dictionary"""
        instance = cls(offset)
        
        if "shape" in data:
            instance.shape = data["shape"]
        if "timbre" in data:
            instance.timbre = data["timbre"]
        if "color" in data:
            instance.color = data["color"]
        if "degrade" in data:
            instance.degrade = data["degrade"]
        if "redux" in data:
            instance.redux = data["redux"]
            
        return instance
        
    @classmethod
    def from_prefixed_dict(cls, data, prefix="synth_", offset=19):
        """Create MacroSynth parameters from a dict with prefixed keys (e.g., synth_shape)"""
        # Extract parameters with the prefix
        params = {}
        for key, value in data.items():
            if key.startswith(prefix):
                # Remove the prefix
                clean_key = key[len(prefix):]
                params[clean_key] = value
                
        return cls(offset, **params)

class M8MacroSynth(M8InstrumentBase):
    def __init__(self, **kwargs):
        # Set type before parent class init
        self.type = 0x01
        
        # MacroSynth specific parameters
        self.name = " "
        self.transpose = 0x4
        self.eq = 0x1
        self.table_tick = 0x01
        self.volume = 0x0
        self.pitch = 0x0
        self.fine_tune = 0x80
        
        # Create parameter group objects with default values
        self.synth = M8MacroSynthParams(offset=19)
        self.filter = M8FilterParams(offset=24)
        self.amp = M8AmpParams(offset=27)
        self.mixer = M8MixerParams(offset=29)
        
        # Apply any non-prefixed kwargs directly to matching properties
        for key, value in kwargs.items():
            if hasattr(self, key) and not key.startswith('_') and not key in ['type', 'synth', 'filter', 'amp', 'mixer']:
                setattr(self, key, value)
            
            # Handle shape, timbre, color, degrade, redux directly
            elif key == 'shape':
                self.synth.shape = value
            elif key == 'timbre':
                self.synth.timbre = value
            elif key == 'color':
                self.synth.color = value
            elif key == 'degrade':
                self.synth.degrade = value
            elif key == 'redux':
                self.synth.redux = value
        
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
        if 'shape' not in kwargs and any(k.startswith('synth_') for k in kwargs):
            self.synth.shape = synth_params.shape
        if 'timbre' not in kwargs and any(k.startswith('synth_') for k in kwargs):
            self.synth.timbre = synth_params.timbre
        if 'color' not in kwargs and any(k.startswith('synth_') for k in kwargs):
            self.synth.color = synth_params.color
        if 'degrade' not in kwargs and any(k.startswith('synth_') for k in kwargs):
            self.synth.degrade = synth_params.degrade
        if 'redux' not in kwargs and any(k.startswith('synth_') for k in kwargs):
            self.synth.redux = synth_params.redux
            
        # Call parent constructor to finish setup
        super().__init__(**kwargs)
    
    def _init_default_parameters(self):
        """Initialize default parameter values for MacroSynth"""
        self.type = 0x01
        self.name = " "
        self.transpose = 0x4
        self.eq = 0x1
        self.table_tick = 0x01
        self.volume = 0x0
        self.pitch = 0x0
        self.fine_tune = 0x80
        
        # Create parameter group objects with default values
        self.synth = M8MacroSynthParams(offset=19)
        self.filter = M8FilterParams(offset=24)
        self.amp = M8AmpParams(offset=27)
        self.mixer = M8MixerParams(offset=29)
        
    def _read_parameters(self, data):
        """Read MacroSynth parameters from binary data"""
        self.type = data[0]
        self.name = data[1:14].decode('utf-8').rstrip('\0')
        
        # Split byte into transpose/eq
        transpose_eq = data[14]
        self.transpose, self.eq = split_byte(transpose_eq)
        
        self.table_tick = data[15]
        self.volume = data[16]
        self.pitch = data[17]
        self.fine_tune = data[18]
        
        # Read synth, filter, amp, and mixer parameters
        self.synth = M8MacroSynthParams.read(data, offset=19)
        self.filter = M8FilterParams.read(data, offset=24)
        self.amp = M8AmpParams.read(data, offset=27)
        self.mixer = M8MixerParams.read(data, offset=29)
    
    def _write_parameters(self):
        """Write MacroSynth parameters to binary data"""
        # Create output buffer
        buffer = bytearray()
        
        # Type
        buffer.append(self.type)
        
        # Name (padded to 13 bytes)
        name_bytes = self.name.encode('utf-8')
        name_bytes = name_bytes[:13]  # Truncate if too long
        name_bytes = name_bytes + bytes([0] * (13 - len(name_bytes)))  # Pad with nulls
        buffer.extend(name_bytes)
        
        # Transpose/EQ (combined into one byte)
        transpose_eq = join_nibbles(self.transpose, self.eq)
        buffer.append(transpose_eq)
        
        # Remaining fields
        buffer.append(self.table_tick)
        buffer.append(self.volume)
        buffer.append(self.pitch)
        buffer.append(self.fine_tune)
        
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
