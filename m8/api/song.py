from m8.core.format import load_format_config

# Load configuration
config = load_format_config()
song_config = config["song"]

# Module-level constants from config
COL_COUNT = song_config["col_count"]       # Number of tracks/columns in the song
ROW_COUNT = song_config["row_count"]       # Maximum number of rows in the song

class M8SongRow:
    """Represents a single row in the M8 song grid with 8 columns of chain references."""
    
    EMPTY_CHAIN = song_config["constants"]["empty_chain"]  # Value indicating no chain is assigned
    
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
