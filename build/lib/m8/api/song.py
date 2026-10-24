"""M8 song matrix — 256 rows × 8 tracks of chain references.

Each row also carries two bookmark bytes that live outside the matrix
(m8-file-parser/src/songs.rs SongSteps):

  bookmarks     bitmask of bookmarked song steps (bit n = track n), 256
                bytes at file offset 0x1A97E
  row_bookmark  whole-row bookmark colour (0 = none), firmware 6.6+, 256
                bytes at file offset 0x1B6C6

M8Project reads/writes both blocks and hands them to M8SongMatrix, the
same "separate attribute merged at write time" pattern as HyperSynth chords.
"""

# Song configuration
SONG_OFFSET = 750
SONG_COL_COUNT = 8
SONG_ROW_COUNT = 256

# Constants
EMPTY_CHAIN = 255

# Module-level constants from config
COL_COUNT = SONG_COL_COUNT
ROW_COUNT = SONG_ROW_COUNT

class M8SongRow:
    """Represents a single row in the M8 song grid with 8 columns of chain references."""

    EMPTY_CHAIN = EMPTY_CHAIN
    
    def __init__(self, bookmarks=0, row_bookmark=0, **kwargs):
        self._data = bytearray([self.EMPTY_CHAIN] * COL_COUNT)
        self.bookmarks = bookmarks
        self.row_bookmark = row_bookmark
        
        # Set any values provided in kwargs
        for col, chain in kwargs.items():
            if col.startswith('col') and col[3:].isdigit():
                col_idx = int(col[3:])
                if 0 <= col_idx < COL_COUNT:
                    self[col_idx] = chain

    @classmethod
    def read(cls, data, bookmarks=0, row_bookmark=0):
        instance = cls(bookmarks=bookmarks, row_bookmark=row_bookmark)
        instance._data = bytearray(data[:COL_COUNT])
        return instance
    
    def clone(self):
        instance = self.__class__(bookmarks=self.bookmarks, row_bookmark=self.row_bookmark)
        instance._data = bytearray(self._data)
        return instance

    def is_bookmarked(self, col):
        """Whether the song step in track `col` (0-7) is bookmarked."""
        if not (0 <= col < COL_COUNT):
            raise IndexError("Index out of range")
        return bool(self.bookmarks & (1 << col))

    def set_bookmark(self, col, on=True):
        if not (0 <= col < COL_COUNT):
            raise IndexError("Index out of range")
        if on:
            self.bookmarks |= 1 << col
        else:
            self.bookmarks &= ~(1 << col) & 0xFF
    
    def __getitem__(self, index):
        if not (0 <= index < COL_COUNT):
            raise IndexError("Index out of range")
        return self._data[index]
    
    def __setitem__(self, index, value):
        if not (0 <= index < COL_COUNT):
            raise IndexError("Index out of range")
        self._data[index] = value
    
    def write(self):
        return bytes(self._data)

    def validate(self, row_index=None):
        """Validate the song row.

        A chain reference is one byte: 0..(CHAIN_COUNT-1) addresses a real
        chain slot, 255 is the empty marker. With CHAIN_COUNT == 255 every
        byte value is now meaningful (0..254 = valid, 255 = empty), so the
        check is essentially "did someone put something other than a u8
        here?" — which can't happen via bytearray semantics, but the loop
        stays in place for explicit-intent (and to catch future capacity
        regressions).
        """
        from m8.api.chain import CHAIN_COUNT
        for col, chain_ref in enumerate(self._data):
            if chain_ref != EMPTY_CHAIN and chain_ref >= CHAIN_COUNT:
                ctx = f" row {row_index}" if row_index is not None else ""
                raise ValueError(
                    f"Invalid chain reference {chain_ref} at{ctx} col {col}: "
                    f"must be 0-{CHAIN_COUNT - 1} or 255 (empty)"
                )

class M8SongMatrix(list):
    """Represents the M8 song grid as a 2D matrix with 256 rows and 8 columns of chain references."""
    
    def __init__(self):
        super().__init__()
        # Initialize with empty rows
        for _ in range(ROW_COUNT):
            self.append(M8SongRow())
    
    @classmethod
    def read(cls, data, bookmarks=None, row_bookmarks=None):
        """`bookmarks` / `row_bookmarks` are the separate 256-byte blocks
        (see module docstring); None leaves them zeroed."""
        instance = cls.__new__(cls)  # Create instance without calling __init__
        list.__init__(instance)  # Initialize the list properly
        
        for i in range(ROW_COUNT):
            start = i * COL_COUNT
            row_data = data[start:start + COL_COUNT]
            instance.append(M8SongRow.read(
                row_data,
                bookmarks=bookmarks[i] if bookmarks else 0,
                row_bookmark=row_bookmarks[i] if row_bookmarks else 0,
            ))
        
        return instance
    
    def clone(self):
        instance = self.__class__()
        instance.clear()  # Remove default items
        
        for row in self:
            instance.append(row.clone())
        
        return instance
    
    def write(self):
        result = bytearray()
        for row in self:
            row_data = row.write()
            result.extend(row_data)
        return bytes(result)

    def write_bookmarks(self):
        return bytes(row.bookmarks & 0xFF for row in self)

    def write_row_bookmarks(self):
        return bytes(row.row_bookmark & 0xFF for row in self)

    def validate(self):
        """Validate the song matrix.

        Raises:
            ValueError: If there are more rows than allowed or invalid chain references
        """
        if len(self) > ROW_COUNT:
            raise ValueError(f"Too many song rows: {len(self)}, maximum is {ROW_COUNT}")

        for i, row in enumerate(self):
            row.validate(row_index=i)
