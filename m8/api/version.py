from m8.utils.bits import split_byte, join_nibbles

class M8Version:
    def __init__(self, major=0, minor=0, patch=0):
        self.major = major
        self.minor = minor
        self.patch = patch
    
    @classmethod
    def read(cls, data):
        instance = cls()
        if len(data) >= 2:
            # First byte contains minor and patch
            minor_patch = data[0]
            instance.minor, instance.patch = split_byte(minor_patch)
            
            # Second byte contains major (in lower nibble)
            major_byte = data[1]
            _, instance.major = split_byte(major_byte)
        
        return instance
    
    def write(self):
        # Combine minor and patch into one byte
        minor_patch = join_nibbles(self.minor, self.patch)
        
        # Major goes in the lower nibble of the second byte
        major_byte = join_nibbles(0, self.major)  # Upper nibble is not used
        
        return bytes([minor_patch, major_byte])
    
    def is_empty(self):
        return self.major == 0 and self.minor == 0 and self.patch == 0
    
    def clone(self):
        return M8Version(self.major, self.minor, self.patch)
    
    def as_dict(self):
        """Convert version to dictionary for serialization"""
        return {
            "major": self.major,
            "minor": self.minor,
            "patch": self.patch
        }
    
    @classmethod
    def from_dict(cls, data):
        """Create version from a dictionary"""
        return cls(
            major=data.get("major", 0),
            minor=data.get("minor", 0),
            patch=data.get("patch", 0)
        )
    
