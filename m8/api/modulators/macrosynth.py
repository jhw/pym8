from m8 import NULL
from m8.api import BLANK
from m8.api.serialization import from_json, to_json
from m8.utils.bits import split_byte, join_nibbles

class M8MacroSynthAHDEnvelope:
    def __init__(self, **kwargs):
        # Default field values
        self.type = 0x0
        self.destination = 0x0
        self.amount = BLANK
        self.attack = NULL
        self.hold = NULL
        self.decay = 0x80
        
        # Apply any provided kwargs
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    @classmethod
    def read(cls, data):
        instance = cls()
        
        # Read type and destination from first byte
        type_dest = data[0]
        instance.type, instance.destination = split_byte(type_dest)
        
        # Read remaining fields
        instance.amount = data[1]
        instance.attack = data[2]
        instance.hold = data[3]
        instance.decay = data[4]
        
        return instance
    
    def write(self):
        # Create output buffer
        buffer = bytearray()
        
        # Type/destination (combined into one byte)
        type_dest = join_nibbles(self.type, self.destination)
        buffer.append(type_dest)
        
        # Remaining fields
        buffer.append(self.amount)
        buffer.append(self.attack)
        buffer.append(self.hold)
        buffer.append(self.decay)
        
        # Pad to ensure proper size
        buffer.extend([NULL])
        
        return bytes(buffer)
    
    def is_empty(self):
        # Consider empty if destination is 0
        return self.destination == 0
    
    def clone(self):
        instance = self.__class__()
        for key, value in vars(self).items():
            setattr(instance, key, value)
        return instance
    
    def as_dict(self):
        """Convert modulator to dictionary for serialization"""
        return {
            "__class__": f"{self.__class__.__module__}.{self.__class__.__name__}",
            **{k: v for k, v in vars(self).items() if not k.startswith('_')}
        }
    
    @classmethod
    def from_dict(cls, data):
        """Create modulator from a dictionary"""
        instance = cls()
        
        for key, value in data.items():
            if key != "__class__" and hasattr(instance, key):
                setattr(instance, key, value)
        
        return instance
    
    def to_json(self, indent=None):
        """Convert modulator to JSON string"""
        return to_json(self, indent=indent)

    @classmethod
    def from_json(cls, json_str):
        """Create an instance from a JSON string"""
        return from_json(json_str, cls)

class M8MacroSynthADSREnvelope:
    def __init__(self, **kwargs):
        # Default field values
        self.type = 0x1
        self.destination = 0x0
        self.amount = BLANK
        self.attack = NULL
        self.decay = 0x80
        self.sustain = 0x80
        self.release = 0x80
        
        # Apply any provided kwargs
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    @classmethod
    def read(cls, data):
        instance = cls()
        
        # Read type and destination from first byte
        type_dest = data[0]
        instance.type, instance.destination = split_byte(type_dest)
        
        # Read remaining fields
        instance.amount = data[1]
        instance.attack = data[2]
        instance.decay = data[3]
        instance.sustain = data[4]
        instance.release = data[5]
        
        return instance
    
    def write(self):
        # Create output buffer
        buffer = bytearray()
        
        # Type/destination (combined into one byte)
        type_dest = join_nibbles(self.type, self.destination)
        buffer.append(type_dest)
        
        # Remaining fields
        buffer.append(self.amount)
        buffer.append(self.attack)
        buffer.append(self.decay)
        buffer.append(self.sustain)
        buffer.append(self.release)
        
        return bytes(buffer)
    
    def is_empty(self):
        # Consider empty if destination is 0
        return self.destination == 0
    
    def clone(self):
        instance = self.__class__()
        for key, value in vars(self).items():
            setattr(instance, key, value)
        return instance
    
    def as_dict(self):
        """Convert modulator to dictionary for serialization"""
        return {
            "__class__": f"{self.__class__.__module__}.{self.__class__.__name__}",
            **{k: v for k, v in vars(self).items() if not k.startswith('_')}
        }
    
    @classmethod
    def from_dict(cls, data):
        """Create modulator from a dictionary"""
        instance = cls()
        
        for key, value in data.items():
            if key != "__class__" and hasattr(instance, key):
                setattr(instance, key, value)
        
        return instance
    
    def to_json(self, indent=None):
        """Convert modulator to JSON string"""
        return to_json(self, indent=indent)

    @classmethod
    def from_json(cls, json_str):
        """Create an instance from a JSON string"""
        return from_json(json_str, cls)

class M8MacroSynthLFO:
    def __init__(self, **kwargs):
        # Default field values
        self.type = 0x3
        self.destination = 0x0
        self.amount = BLANK
        self.shape = NULL
        self.trigger = NULL
        self.freq = 0x10
        self.retrigger = NULL
        
        # Apply any provided kwargs
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    @classmethod
    def read(cls, data):
        instance = cls()
        
        # Read type and destination from first byte
        type_dest = data[0]
        instance.type, instance.destination = split_byte(type_dest)
        
        # Read remaining fields
        instance.amount = data[1]
        instance.shape = data[2]
        instance.trigger = data[3]
        instance.freq = data[4]
        instance.retrigger = data[5]
        
        return instance
    
    def write(self):
        # Create output buffer
        buffer = bytearray()
        
        # Type/destination (combined into one byte)
        type_dest = join_nibbles(self.type, self.destination)
        buffer.append(type_dest)
        
        # Remaining fields
        buffer.append(self.amount)
        buffer.append(self.shape)
        buffer.append(self.trigger)
        buffer.append(self.freq)
        buffer.append(self.retrigger)
        
        return bytes(buffer)
    
    def is_empty(self):
        # Consider empty if destination is 0
        return self.destination == 0
    
    def clone(self):
        instance = self.__class__()
        for key, value in vars(self).items():
            setattr(instance, key, value)
        return instance
    
    def as_dict(self):
        """Convert modulator to dictionary for serialization"""
        return {
            "__class__": f"{self.__class__.__module__}.{self.__class__.__name__}",
            **{k: v for k, v in vars(self).items() if not k.startswith('_')}
        }
    
    @classmethod
    def from_dict(cls, data):
        """Create modulator from a dictionary"""
        instance = cls()
        
        for key, value in data.items():
            if key != "__class__" and hasattr(instance, key):
                setattr(instance, key, value)
        
        return instance
    
    def to_json(self, indent=None):
        """Convert modulator to JSON string"""
        return to_json(self, indent=indent)

    @classmethod
    def from_json(cls, json_str):
        """Create an instance from a JSON string"""
        return from_json(json_str, cls)
