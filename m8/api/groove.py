# m8/api/groove.py
"""M8 grooves — 32 timing-curve patterns.

Each groove is 16 bytes of timing offsets (one per step in a 16-step
pattern). Value 0xFF marks the end of the active region — anything
after the first 0xFF in a groove is "off the end" of the pattern.

32 grooves × 16 bytes = 512 bytes at file offset 0xEE (238).

The M8's GRV FX command selects which groove drives a track's timing.
A groove with all 0xFF bytes is effectively a no-op (straight timing).

Firmware 6.5+ adds a per-groove PPQN (tick resolution) byte. It isn't
stored with the steps: the 32 PPQN bytes sit in their own block at file
offset 0x1B6A6, just after the EQs. M8Project reads/writes that block and
hands it to M8Grooves; each groove exposes it as `ppqn`.
"""

from enum import IntEnum

GROOVE_STEPS = 16
GROOVE_COUNT = 32
GROOVE_BYTES = GROOVE_STEPS
EMPTY_STEP = 0xFF


class M8GroovePPQN(IntEnum):
    """Groove tick resolution (firmware 6.5+). Mirrors songs.rs Groove::active_ppqn."""
    PPQN_24 = 0
    PPQN_48 = 1
    PPQN_96 = 2
    PPQN_192 = 3


_PPQN_TICKS = {M8GroovePPQN.PPQN_24: 24, M8GroovePPQN.PPQN_48: 48,
               M8GroovePPQN.PPQN_96: 96, M8GroovePPQN.PPQN_192: 192}


class M8Groove:
    """One 16-step timing curve. Step values are timing offsets; 0xFF
    terminates the active portion of the pattern."""

    BYTES = GROOVE_BYTES
    STEPS = GROOVE_STEPS

    def __init__(self, steps=None, ppqn=M8GroovePPQN.PPQN_24):
        self._data = bytearray([EMPTY_STEP] * self.STEPS)
        if steps is not None:
            for i, v in enumerate(steps[:self.STEPS]):
                self._data[i] = int(v) & 0xFF
        self.ppqn = ppqn

    @property
    def ppqn(self):
        """Raw PPQN byte (an M8GroovePPQN value on well-formed files)."""
        return self._ppqn

    @ppqn.setter
    def ppqn(self, value):
        self._ppqn = int(M8GroovePPQN(value))

    def active_ppqn(self):
        """Ticks per quarter note; unknown values fall back to 24, as in Rust."""
        return _PPQN_TICKS.get(self._ppqn, 24)

    def __len__(self):
        return self.STEPS

    def __getitem__(self, i):
        if not 0 <= i < self.STEPS:
            raise IndexError(f"groove step {i} out of range [0, {self.STEPS - 1}]")
        return self._data[i]

    def __setitem__(self, i, value):
        if not 0 <= i < self.STEPS:
            raise IndexError(f"groove step {i} out of range [0, {self.STEPS - 1}]")
        if hasattr(value, "value"):
            value = value.value
        self._data[i] = int(value) & 0xFF

    def __iter__(self):
        return iter(self._data)

    def active_steps(self):
        """Steps up to (and not including) the first 0xFF terminator."""
        for i, v in enumerate(self._data):
            if v == EMPTY_STEP:
                return list(self._data[:i])
        return list(self._data)

    def is_empty(self):
        """All bytes are 0xFF (no active steps)."""
        return all(b == EMPTY_STEP for b in self._data)

    @classmethod
    def read(cls, data, ppqn=0):
        instance = cls.__new__(cls)
        instance._data = bytearray(data[:cls.BYTES])
        # Raw on read — a file byte outside the enum still round-trips.
        instance._ppqn = ppqn
        return instance

    def write(self):
        return bytes(self._data)

    def clone(self):
        instance = self.__class__.__new__(self.__class__)
        instance._data = bytearray(self._data)
        instance._ppqn = self._ppqn
        return instance

    def to_dict(self):
        try:
            ppqn = M8GroovePPQN(self._ppqn).name
        except ValueError:
            ppqn = self._ppqn
        return {"steps": list(self._data), "ppqn": ppqn}

    @classmethod
    def from_dict(cls, d):
        ppqn = d.get("ppqn", M8GroovePPQN.PPQN_24)
        if isinstance(ppqn, str):
            ppqn = M8GroovePPQN[ppqn]
        return cls(steps=d.get("steps", []), ppqn=ppqn)


class M8Grooves(list):
    """32 grooves at file offset 0xEE (238)."""

    COUNT = GROOVE_COUNT
    TOTAL_BYTES = GROOVE_COUNT * GROOVE_BYTES
    PPQN_BYTES = GROOVE_COUNT  # one byte per groove, stored separately

    def __init__(self):
        super().__init__()
        for _ in range(self.COUNT):
            self.append(M8Groove())

    @classmethod
    def read(cls, data, version=None, ppqn=None):
        """`ppqn` is the separate 32-byte PPQN block (firmware 6.5+); None
        leaves every groove at PPQN_24."""
        instance = cls.__new__(cls)
        list.__init__(instance)
        for i in range(cls.COUNT):
            start = i * GROOVE_BYTES
            block = data[start:start + GROOVE_BYTES]
            if len(block) < GROOVE_BYTES:
                block = block + bytes([EMPTY_STEP] * (GROOVE_BYTES - len(block)))
            instance.append(M8Groove.read(block, ppqn=ppqn[i] if ppqn else 0))
        return instance

    def write(self):
        return b"".join(g.write() for g in self)

    def write_ppqn(self):
        """The 32-byte PPQN block, written by M8Project at its own offset."""
        return bytes(g.ppqn for g in self)

    def clone(self):
        instance = self.__class__.__new__(self.__class__)
        list.__init__(instance)
        for g in self:
            instance.append(g.clone())
        return instance

    def to_dict(self):
        return [g.to_dict() for g in self]

    @classmethod
    def from_dict(cls, items):
        instance = cls.__new__(cls)
        list.__init__(instance)
        for item in items[:cls.COUNT]:
            instance.append(M8Groove.from_dict(item))
        while len(instance) < cls.COUNT:
            instance.append(M8Groove())
        return instance
