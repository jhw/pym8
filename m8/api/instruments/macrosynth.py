from m8.api.instruments import M8InstrumentBase
from m8.utils.bits import split_byte, join_nibbles

class M8MacroSynthParams:
    def __init__(self, **kwargs):
        # Default field values
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
        self.mixer_pan = 0x80
        self.mixer_dry = 0xC0
        self.mixer_chorus = 0x0
        self.mixer_delay = 0x0
        self.mixer_reverb = 0x0
        
        # Apply any provided kwargs
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    @classmethod
    def read(cls, data):
        instance = cls()
        
        # Read fields from data
        instance.type = data[0]
        instance.name = data[1:14].decode('utf-8').rstrip('\0')
        
        # Split byte into transpose/eq
        transpose_eq = data[14]
        instance.transpose, instance.eq = split_byte(transpose_eq)
        
        instance.table_tick = data[15]
        instance.volume = data[16]
        instance.pitch = data[17]
        instance.fine_tune = data[18]
        instance.shape = data[19]
        instance.timbre = data[20]
        instance.color = data[21]
        instance.degrade = data[22]
        instance.redux = data[23]
        instance.filter_type = data[24]
        instance.filter_cutoff = data[25]
        instance.filter_resonance = data[26]
        instance.amp_level = data[27]
        instance.amp_limit = data[28]
        instance.mixer_pan = data[29]
        instance.mixer_dry = data[30]
        instance.mixer_chorus = data[31]
        instance.mixer_delay = data[32]
        instance.mixer_reverb = data[33]
        
        return instance
    
    def write(self):
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
        buffer.append(self.mixer_pan)
        buffer.append(self.mixer_dry)
        buffer.append(self.mixer_chorus)
        buffer.append(self.mixer_delay)
        buffer.append(self.mixer_reverb)
        
        return bytes(buffer)
    
    def is_empty(self):
        # Consider params empty if name is blank and key parameters are default
        return (self.name.strip() == "" and 
                self.volume == 0x0 and 
                self.shape == 0x0)
    
    def clone(self):
        instance = self.__class__()
        for key, value in vars(self).items():
            setattr(instance, key, value)
        return instance
    
    def as_dict(self):
        """Convert parameters to dictionary for serialization"""
        return {
            **{k: v for k, v in vars(self).items() if not k.startswith('_')}
        }
    
    @classmethod
    def from_dict(cls, data):
        """Create parameters from a dictionary"""
        instance = cls()
        
        for key, value in data.items():
            if key != "__class__" and hasattr(instance, key):
                setattr(instance, key, value)
        
        return instance
    
class M8MacroSynth(M8InstrumentBase):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
