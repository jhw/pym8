from m8.api import split_byte, join_nibbles

class M8Version:
    """Handles M8 firmware semantic versioning (major.minor.patch) for file format compatibility."""
    
    MINOR_PATCH_OFFSET = 0
    MAJOR_BYTE_OFFSET = 1
    UPPER_NIBBLE_POS = 0
    LOWER_NIBBLE_POS = 1
    BLOCK_SIZE = 2
    
    def __init__(self, major=0, minor=0, patch=0):
        self.major = major
        self.minor = minor
        self.patch = patch
    
    def __repr__(self):
        return f"{self.major}.{self.minor}.{self.patch}"
    
    @classmethod
    def read(cls, data):
        instance = cls()
        if len(data) >= cls.BLOCK_SIZE:
            # First byte contains minor and patch
            minor_patch = data[cls.MINOR_PATCH_OFFSET]
            instance.minor, instance.patch = split_byte(minor_patch)
            
            # Second byte contains major (in lower nibble)
            major_byte = data[cls.MAJOR_BYTE_OFFSET]
            _, instance.major = split_byte(major_byte)
        
        return instance
    
    def write(self):
        # Combine minor and patch into one byte
        minor_patch = join_nibbles(self.minor, self.patch)
        
        # Major goes in the lower nibble of the second byte
        major_byte = join_nibbles(0, self.major)
        
        return bytes([minor_patch, major_byte])
    
    def is_empty(self):
        return self.major == 0 and self.minor == 0 and self.patch == 0
    
    def clone(self):
        return M8Version(self.major, self.minor, self.patch)
    
    @classmethod
    def from_str(cls, version_str):
        if isinstance(version_str, str):
            parts = version_str.split('.')
            try:
                major = int(parts[0]) if len(parts) > 0 else 0
                minor = int(parts[1]) if len(parts) > 1 else 0
                patch = int(parts[2]) if len(parts) > 2 else 0
                return cls(major=major, minor=minor, patch=patch)
            except (ValueError, IndexError):
                return cls()
        else:
            return cls()
