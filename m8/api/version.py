from m8.api import split_byte, join_nibbles

class M8Version:
    """Represents an M8 version number.
    
    Handles serialization and deserialization of semantic version numbers (major.minor.patch)
    used to track compatibility between M8 firmware versions and file formats.
    """
    
    # Define byte positions
    MINOR_PATCH_OFFSET = 0
    MAJOR_BYTE_OFFSET = 1
    
    # Define nibble positions within bytes
    UPPER_NIBBLE_POS = 0  # Upper 4 bits
    LOWER_NIBBLE_POS = 1  # Lower 4 bits
    
    # Define block size
    BLOCK_SIZE = 2
    
    def __init__(self, major=0, minor=0, patch=0):
        """Initialize a version with major, minor, and patch numbers.
        
        Args:
            major: Major version number (0-15)
            minor: Minor version number (0-15)
            patch: Patch version number (0-15)
        """
        self.major = major
        self.minor = minor
        self.patch = patch
    
    def __repr__(self):
        """Return string representation of version.
        
        Returns:
            str: Version in format "major.minor.patch"
        """
        return f"{self.major}.{self.minor}.{self.patch}"
    
    @classmethod
    def read(cls, data):
        """Create a version from binary data.
        
        Args:
            data: Binary data containing version information
            
        Returns:
            M8Version: New instance with values from the binary data
        """
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
        """Convert the version to binary data.
        
        Returns:
            bytes: Binary representation of the version
        """
        # Combine minor and patch into one byte
        minor_patch = join_nibbles(self.minor, self.patch)
        
        # Major goes in the lower nibble of the second byte
        major_byte = join_nibbles(0, self.major)  # Upper nibble is not used
        
        return bytes([minor_patch, major_byte])
    
    def is_empty(self):
        """Check if this version is empty (all zeros).
        
        Returns:
            bool: True if the version is 0.0.0, False otherwise
        """
        return self.major == 0 and self.minor == 0 and self.patch == 0
    
    def clone(self):
        """Create a copy of this version.
        
        Returns:
            M8Version: New instance with the same values
        """
        return M8Version(self.major, self.minor, self.patch)
    
    @classmethod
    def from_str(cls, version_str):
        """Create version from a string.
        
        Args:
            version_str: String in format "major.minor.patch"
            
        Returns:
            M8Version: New instance parsed from the string, or default 0.0.0 if parsing fails
        """
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
