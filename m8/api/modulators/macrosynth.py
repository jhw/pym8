from m8.api.modulators import M8ModulatorBase

class M8MacroSynthAHDEnvelope(M8ModulatorBase):
    def __init__(self, **kwargs):
        # Default field values
        self.type = 0x0
        self.destination = 0x0
        self.amount = 0xFF
        self.attack = 0x0
        self.hold = 0x0
        self.decay = 0x80
        
        # Apply any provided kwargs
        super().__init__(**kwargs)
    
    @classmethod
    def read(cls, data):
        instance = super().read(data)
        
        # Read specific fields for AHD envelope
        if len(data) > 2:
            instance.attack = data[2]
        if len(data) > 3:
            instance.hold = data[3]
        if len(data) > 4:
            instance.decay = data[4]
        
        return instance
    
    def write(self):
        # Get the common header (type/dest and amount)
        buffer = bytearray(super().write())
        
        # Add AHD-specific fields
        buffer.append(self.attack)
        buffer.append(self.hold)
        buffer.append(self.decay)
        
        # Pad to ensure proper size
        while len(buffer) < 6:
            buffer.append(0x0)
        
        return bytes(buffer)

class M8MacroSynthADSREnvelope(M8ModulatorBase):
    def __init__(self, **kwargs):
        # Default field values
        self.type = 0x1
        self.destination = 0x0
        self.amount = 0xFF
        self.attack = 0x0
        self.decay = 0x80
        self.sustain = 0x80
        self.release = 0x80
        
        # Apply any provided kwargs
        super().__init__(**kwargs)
    
    @classmethod
    def read(cls, data):
        instance = super().read(data)
        
        # Read specific fields for ADSR envelope
        if len(data) > 2:
            instance.attack = data[2]
        if len(data) > 3:
            instance.decay = data[3]
        if len(data) > 4:
            instance.sustain = data[4]
        if len(data) > 5:
            instance.release = data[5]
        
        return instance
    
    def write(self):
        # Get the common header (type/dest and amount)
        buffer = bytearray(super().write())
        
        # Add ADSR-specific fields
        buffer.append(self.attack)
        buffer.append(self.decay)
        buffer.append(self.sustain)
        buffer.append(self.release)
        
        return bytes(buffer)

class M8MacroSynthLFO(M8ModulatorBase):
    def __init__(self, **kwargs):
        # Default field values
        self.type = 0x3
        self.destination = 0x0
        self.amount = 0xFF
        self.shape = 0x0
        self.trigger = 0x0
        self.freq = 0x10
        self.retrigger = 0x0
        
        # Apply any provided kwargs
        super().__init__(**kwargs)
    
    @classmethod
    def read(cls, data):
        instance = super().read(data)
        
        # Read specific fields for LFO
        if len(data) > 2:
            instance.shape = data[2]
        if len(data) > 3:
            instance.trigger = data[3]
        if len(data) > 4:
            instance.freq = data[4]
        if len(data) > 5:
            instance.retrigger = data[5]
        
        return instance
    
    def write(self):
        # Get the common header (type/dest and amount)
        buffer = bytearray(super().write())
        
        # Add LFO-specific fields
        buffer.append(self.shape)
        buffer.append(self.trigger)
        buffer.append(self.freq)
        buffer.append(self.retrigger)
        
        return bytes(buffer)
