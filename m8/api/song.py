# Song configuration
SONG_OFFSET = 750
SONG_COL_COUNT = 8
SONG_ROW_COUNT = 255

# Constants
EMPTY_CHAIN = 255

# Module-level constants from config
COL_COUNT = SONG_COL_COUNT
ROW_COUNT = SONG_ROW_COUNT

class M8SongRow:
    """Represents a single row in the M8 song grid with 8 columns of chain references."""

    EMPTY_CHAIN = EMPTY_CHAIN
    
    def __init__(self, **kwargs):
        self._data = bytearray([self.EMPTY_CHAIN] * COL_COUNT)
        
        # Set any values provided in kwargs
        for col, chain in kwargs.items():
            if col.startswith('col') and col[3:].isdigit():
                col_idx = int(col[3:])
                if 0 <= col_idx < COL_COUNT:
                    self[col_idx] = chain

    @classmethod
    def read(cls, data):
        instance = cls()
        instance._data = bytearray(data[:COL_COUNT])
        return instance
    
    def clone(self):
        instance = self.__class__()
        instance._data = bytearray(self._data)
        return instance
    
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

        Args:
            row_index: Optional row index for error messages

        Raises:
            ValueError: If chain reference is invalid
        """
        # Chain references must be 0-127 (valid chains) or 255 (empty)
        # Values 128-254 are invalid
        for col, chain_ref in enumerate(self._data):
            if chain_ref != EMPTY_CHAIN and chain_ref > 127:
                ctx = f" row {row_index}" if row_index is not None else ""
                raise ValueError(f"Invalid chain reference {chain_ref} at{ctx} col {col}: must be 0-127 or 255 (empty)")

class M8SongMatrix(list):
    """Represents the M8 song grid as a 2D matrix with 255 rows and 8 columns of chain references."""
    
    def __init__(self):
        super().__init__()
        # Initialize with empty rows
        for _ in range(ROW_COUNT):
            self.append(M8SongRow())
    
    @classmethod
    def read(cls, data):
        instance = cls.__new__(cls)  # Create instance without calling __init__
        list.__init__(instance)  # Initialize the list properly
        
        for i in range(ROW_COUNT):
            start = i * COL_COUNT
            row_data = data[start:start + COL_COUNT]
            instance.append(M8SongRow.read(row_data))
        
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

    def validate(self):
        """Validate the song matrix.

        Raises:
            ValueError: If there are more rows than allowed or invalid chain references
        """
        if len(self) > ROW_COUNT:
            raise ValueError(f"Too many song rows: {len(self)}, maximum is {ROW_COUNT}")

        for i, row in enumerate(self):
            row.validate(row_index=i)
