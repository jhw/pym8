from m8.api import split_byte, join_nibbles
from m8.api.instruments import M8InstrumentBase, M8MixerParams

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
        self.shape = 0x0
        self.timbre = 0x80
        self.color = 0x80
        self.degrade = 0x0
        self.redux = 0x0
        self.filter_type = 0x0
        self.filter_cutoff = 0xFF
        self.filter_resonance = 0x0
        self.amp_level = 0x0
        self.amp_limit = 0x0
        
        # Create mixer parameters using prefixed parameter extraction
        self.mixer = M8MixerParams.from_prefixed_dict(kwargs, offset=29)
        
        # Call parent constructor to finish setup with remaining kwargs
        # (We don't need to modify kwargs as from_prefixed_dict doesn't modify the input)
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
        self.shape = 0x0
        self.timbre = 0x80
        self.color = 0x80
        self.degrade = 0x0
        self.redux = 0x0
        self.filter_type = 0x0
        self.filter_cutoff = 0xFF
        self.filter_resonance = 0x0
        self.amp_level = 0x0
        self.amp_limit = 0x0
        
        # Create mixer parameters
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
        self.shape = data[19]
        self.timbre = data[20]
        self.color = data[21]
        self.degrade = data[22]
        self.redux = data[23]
        self.filter_type = data[24]
        self.filter_cutoff = data[25]
        self.filter_resonance = data[26]
        self.amp_level = data[27]
        self.amp_limit = data[28]
        # Read mixer parameters
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
        buffer.append(self.shape)
        buffer.append(self.timbre)
        buffer.append(self.color)
        buffer.append(self.degrade)
        buffer.append(self.redux)
        buffer.append(self.filter_type)
        buffer.append(self.filter_cutoff)
        buffer.append(self.filter_resonance)
        buffer.append(self.amp_level)
        buffer.append(self.amp_limit)
        # Add mixer parameters
        buffer.extend(self.mixer.write())
        
        return bytes(buffer)
    
    def is_empty(self):
        """Check if the MacroSynth instrument is empty"""
        return (self.name.strip() == "" and 
                self.volume == 0x0 and 
                self.shape == 0x0)

    def as_dict(self):
        """Convert MacroSynth to dictionary for serialization"""
        # Use parent implementation, which now correctly handles
        # nested objects with as_dict methods
        return super().as_dict()
