from m8.api import split_byte, join_nibbles

class M8Version:
    def __init__(self, major=0, minor=0, patch=0):
        self.major = major
        self.minor = minor
        self.patch = patch
    
    def __repr__(self):
        """Return string representation of version"""
        return f"{self.major}.{self.minor}.{self.patch}"
    
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
    
    @classmethod
    def from_str(cls, version_str):
        """Create version from a string"""
        if isinstance(version_str, str):
            # Parse from string like "1.2.3"
            parts = version_str.split('.')
            try:
                major = int(parts[0]) if len(parts) > 0 else 0
                minor = int(parts[1]) if len(parts) > 1 else 0
                patch = int(parts[2]) if len(parts) > 2 else 0
                return cls(major=major, minor=minor, patch=patch)
            except (ValueError, IndexError):
                # If parsing fails, return default version
                return cls()
        else:
            # Default for any other input
            return cls()
