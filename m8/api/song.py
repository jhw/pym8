from m8.core.format import load_format_config
from m8.core.validation import M8ValidationResult

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
    
    def is_empty(self):
        """Check if this song row is empty.
        
        Uses a lenient approach that checks if all chain references equal the M8 empty chain value (0xFF).
        This approach focuses on the M8's definition of emptiness rather than validating against
        external references, maintaining consistency with other emptiness checks in the codebase.
        """
        return all(chain == self.EMPTY_CHAIN for chain in self._data)
    
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
    
    def validate_references_chains(self, chains, result=None):
        if result is None:
            result = M8ValidationResult(context="song_row.chains")
            
        if not self.is_empty():
            for col_idx in range(COL_COUNT):
                chain_idx = self[col_idx]
                if chain_idx != self.EMPTY_CHAIN and (
                    chain_idx >= len(chains) or 
                    chains[chain_idx].is_empty()
                ):
                    result.add_error(
                        f"Column {col_idx} references non-existent or empty "
                        f"chain {chain_idx}",
                        f"col[{col_idx}]"
                    )
                    
        return result
    
    def as_dict(self):
        # Only include non-blank chain references
        chains = []
        for i in range(COL_COUNT):
            if self[i] != self.EMPTY_CHAIN:
                chains.append({"col": i, "chain": self[i]})
        
        return {
            "chains": chains
        }
    
    @classmethod
    def from_dict(cls, data):
        instance = cls()
        
        # Set chain references
        if "chains" in data:
            for chain_ref in data["chains"]:
                col = chain_ref["col"]
                chain = chain_ref["chain"]
                if 0 <= col < COL_COUNT:
                    instance[col] = chain
        
        return instance

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
    
    def is_empty(self):
        """Check if this song matrix is empty.
        
        A song matrix is considered empty if all of its rows are empty.
        This lenient approach delegates to each row's is_empty() method,
        maintaining consistency in emptiness definitions throughout the codebase.
        """
        return all(row.is_empty() for row in self)
    
    def write(self):
        result = bytearray()
        for row in self:
            row_data = row.write()
            result.extend(row_data)
        return bytes(result)
    
    def validate_references_chains(self, chains, result=None):
        if result is None:
            result = M8ValidationResult(context="song_matrix.chains")
            
        for row_idx, row in enumerate(self):
            row_result = row.validate_references_chains(chains)
            if not row_result.valid:
                # Merge errors with the proper context
                result.merge(row_result, f"row[{row_idx}]")
                
        return result
    
    def as_list(self):
        # Only include non-empty rows for sparse representation
        result = []
        for i, row in enumerate(self):
            if not row.is_empty():
                row_dict = row.as_dict()
                row_dict["index"] = i
                result.append(row_dict)
        
        return result
    
    @classmethod
    def from_list(cls, items):
        instance = cls()
        
        # Set rows
        if items:
            for row_data in items:
                row_idx = row_data.get("index", 0)
                if 0 <= row_idx < ROW_COUNT:
                    instance[row_idx] = M8SongRow.from_dict(row_data)
        
        return instance
