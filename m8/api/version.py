# m8/api/version.py
from m8.api import M8Block, split_byte, join_nibbles

class M8Version:
    """Represents the M8 firmware version used to create a file."""
    
    def __init__(self, major=4, minor=0, patch=33):
        """Initialize version with default values matching 4.0.33 (TEMPLATE-5-0-1-4-0-33)."""
        self.major = major
        self.minor = minor
        self.patch = patch
        
    @classmethod
    def read(cls, data):
        """Read version information from data buffer."""
        # File bytes are stored as [patch].[major].[minor].[zero]
        # but we want to represent it as [major].[minor].[patch]
        instance = cls()
        
        # Typically 4 bytes, but read safely
        if len(data) >= 1:
            # File's first byte is patch
            instance.patch = data[0]
        if len(data) >= 2:
            # File's second byte is major
            instance.major = data[1]
        if len(data) >= 3:
            # File's third byte is minor
            instance.minor = data[2]
            
        return instance
        
    def write(self):
        """Convert version to binary data."""
        # We store as [patch].[major].[minor].[zero] in the file
        # even though we represent it as [major].[minor].[patch] in the code
        return bytes([self.patch, self.major, self.minor, 0]) # Typically 4 bytes
    
    def __str__(self):
        """String representation as major.minor.patch."""
        return f"{self.major}.{self.minor}.{self.patch}"
        
    @classmethod
    def from_str(cls, version_str):
        """Create version from a string like '4.0.33'."""
        # Handle None or empty strings
        if not version_str or version_str == 'None':
            return cls()  # Return default version 4.0.33 (TEMPLATE-5-0-1-4-0-33)
            
        parts = version_str.split('.')
        
        major = int(parts[0]) if len(parts) > 0 else 4
        minor = int(parts[1]) if len(parts) > 1 else 0
        patch = int(parts[2]) if len(parts) > 2 else 33
        
        return cls(major, minor, patch)
