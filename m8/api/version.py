# m8/api/version.py
"""M8 firmware version handling with ordered comparison support."""


class M8Version:
    """Represents the M8 firmware version used to create a file."""

    def __init__(self, major=6, minor=0, patch=17):
        """Initialize version. Defaults match TEMPLATE-6-2-1.m8s (firmware 6.0.17)."""
        self.major = major
        self.minor = minor
        self.patch = patch

    @classmethod
    def read(cls, data):
        """Read version from a buffer where bytes are laid out [patch, major, minor, 0]."""
        instance = cls()
        if len(data) >= 1:
            instance.patch = data[0]
        if len(data) >= 2:
            instance.major = data[1]
        if len(data) >= 3:
            instance.minor = data[2]
        return instance

    def write(self):
        return bytes([self.patch, self.major, self.minor, 0])

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
        minor = int(parts[1]) if len(parts) > 1 else 0
        patch = int(parts[2]) if len(parts) > 2 else 17
        return cls(major, minor, patch)
