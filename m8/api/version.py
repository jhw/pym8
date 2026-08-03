# m8/api/version.py
"""M8 firmware version handling with ordered comparison support."""


class M8Version:
    """Represents the M8 firmware version used to create a file."""

    def __init__(self, major=6, minor=1, patch=1):
        """Initialize version. Defaults match TEMPLATE-6-2-1.m8s (firmware 6.2.1)."""
        self.major = major
        self.minor = minor
        self.patch = patch
        # Trailing 2 bytes of the on-disk version block. m8-file-parser's
        # reader skips them on read and always writes 0x00, 0x10 on write
        # (comment: "why? don't know, but borked result if not written") —
        # but real device files (e.g. the bundled template) carry 0x00, 0x00
        # there. Preserved verbatim so an untouched read->write round-trips
        # byte-identical instead of guessing at a fixed value.
        self._reserved = bytes([0, 0])

    @classmethod
    def read(cls, data):
        """Read version from a buffer laid out [(minor<<4)|patch, major, reserved, reserved].

        Byte 0 is nibble-packed: high nibble is minor, low nibble is patch —
        matching m8-file-parser's Version::from_reader (version.rs). Byte 1's
        low nibble is major.
        """
        instance = cls()
        if len(data) >= 1:
            instance.minor = (data[0] >> 4) & 0x0F
            instance.patch = data[0] & 0x0F
        if len(data) >= 2:
            instance.major = data[1] & 0x0F
        if len(data) >= 4:
            instance._reserved = bytes(data[2:4])
        return instance

    def write(self):
        byte0 = ((self.minor & 0x0F) << 4) | (self.patch & 0x0F)
        byte1 = self.major & 0x0F
        return bytes([byte0, byte1]) + self._reserved

    def clone(self):
        instance = self.__class__(self.major, self.minor, self.patch)
        instance._reserved = self._reserved
        return instance

    def tuple(self):
        """Return (major, minor, patch) for ordered comparison."""
        return (self.major, self.minor, self.patch)

    def __eq__(self, other):
        if isinstance(other, M8Version):
            return self.tuple() == other.tuple()
        if isinstance(other, tuple):
            return self.tuple() == other
        return NotImplemented

    def __lt__(self, other):
        return self.tuple() < self._coerce(other)

    def __le__(self, other):
        return self.tuple() <= self._coerce(other)

    def __gt__(self, other):
        return self.tuple() > self._coerce(other)

    def __ge__(self, other):
        return self.tuple() >= self._coerce(other)

    def __hash__(self):
        return hash(self.tuple())

    @staticmethod
    def _coerce(other):
        if isinstance(other, M8Version):
            return other.tuple()
        if isinstance(other, tuple):
            return other
        raise TypeError(f"Cannot compare M8Version with {type(other).__name__}")

    def __str__(self):
        return f"{self.major}.{self.minor}.{self.patch}"

    def __repr__(self):
        return f"M8Version({self.major}, {self.minor}, {self.patch})"

    @classmethod
    def from_str(cls, version_str):
        """Parse a version string like '4.0.33'. Empty or 'None' returns the default."""
        if not version_str or version_str == 'None':
            return cls()
        parts = version_str.split('.')
        major = int(parts[0]) if len(parts) > 0 else 6
        minor = int(parts[1]) if len(parts) > 1 else 1
        patch = int(parts[2]) if len(parts) > 2 else 1
        return cls(major, minor, patch)
