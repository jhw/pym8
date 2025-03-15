from m8.api import M8ValidationError

# Module-level constants
COL_COUNT = 8       # Number of tracks/columns in the song
ROW_COUNT = 255     # Maximum number of rows in the song

class M8SongRow:
    """Represents a single row in the M8 song grid.
    
    Each row contains up to 8 columns that can reference chains to be played.
    Song rows are the building blocks of the M8 song sequencer.
    """
    
    # Class-level constants
    EMPTY_CHAIN = 0xFF  # Value indicating no chain is assigned
    
    def __init__(self, **kwargs):
        """Initialize a song row with optional chain assignments.
        
        Args:
            **kwargs: Optional column assignments in format col0=chain_idx, col1=chain_idx, etc.
        """
        self._data = bytearray([self.EMPTY_CHAIN] * COL_COUNT)
        
        # Set any values provided in kwargs
        for col, chain in kwargs.items():
            if col.startswith('col') and col[3:].isdigit():
                col_idx = int(col[3:])
                if 0 <= col_idx < COL_COUNT:
                    self[col_idx] = chain

    @classmethod
    def read(cls, data):
        """Create a song row from binary data.
        
        Args:
            data: Binary data containing a song row
            
        Returns:
            M8SongRow: New instance with values from the binary data
        """
        instance = cls()
        instance._data = bytearray(data[:COL_COUNT])
        return instance
    
    def clone(self):
        """Create a deep copy of this song row.
        
        Returns:
            M8SongRow: New instance with the same values
        """
        instance = self.__class__()
        instance._data = bytearray(self._data)
        return instance
    
    def is_empty(self):
        """Check if this song row is empty (no chain assignments).
        
        Returns:
            bool: True if all columns have EMPTY_CHAIN, False otherwise
        """
        return all(chain == self.EMPTY_CHAIN for chain in self._data)
    
    def __getitem__(self, index):
        """Get the chain index at the specified column.
        
        Args:
            index: Column index (0-7)
            
        Returns:
            int: Chain index or EMPTY_CHAIN
            
        Raises:
            IndexError: If the index is out of range
        """
        if not (0 <= index < COL_COUNT):
            raise IndexError("Index out of range")
        return self._data[index]
    
    def __setitem__(self, index, value):
        """Set the chain index at the specified column.
        
        Args:
            index: Column index (0-7)
            value: Chain index to set
            
        Raises:
            IndexError: If the index is out of range
        """
        if not (0 <= index < COL_COUNT):
            raise IndexError("Index out of range")
        self._data[index] = value
    
    def write(self):
        """Convert the song row to binary data.
        
        Returns:
            bytes: Binary representation of the song row
        """
        return bytes(self._data)
    
    def validate_chains(self, chains):
        """Validate that all referenced chains exist.
        
        Args:
            chains: List of chains to validate against
            
        Raises:
            M8ValidationError: If a column references a non-existent or empty chain
        """
        if not self.is_empty():
            for col_idx in range(COL_COUNT):
                chain_idx = self[col_idx]
                if chain_idx != self.EMPTY_CHAIN and (
                    chain_idx >= len(chains) or 
                    chains[chain_idx].is_empty()
                ):
                    raise M8ValidationError(
                        f"Column {col_idx} references non-existent or empty "
                        f"chain {chain_idx}"
                    )
    
    def as_dict(self):
        """Convert song row to dictionary for serialization.
        
        Only includes non-empty chain references.
        
        Returns:
            dict: Dictionary representation of the song row
        """
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
        """Create a song row from a dictionary.
        
        Args:
            data: Dictionary containing song row data
            
        Returns:
            M8SongRow: New instance with values from the dictionary
        """
        instance = cls()
        
        # Set chain references
        if "chains" in data:
            for chain_ref in data["chains"]:
                col = chain_ref.get("col", 0)
                chain = chain_ref.get("chain", cls.EMPTY_CHAIN)
                if 0 <= col < COL_COUNT:
                    instance[col] = chain
        
        return instance

class M8SongMatrix(list):
    """Represents the entire song grid in the M8 tracker.
    
    A song matrix is a collection of rows, where each row contains
    multiple columns that reference chains. The matrix determines
    the song's arrangement and structure.
    
    The song grid is organized as a 2D matrix with:
    - Up to 255 rows (vertical position in the song)
    - 8 columns (tracks) per row
    
    Each cell in the matrix can reference a chain to be played, or be empty.
    The song playback moves vertically through the rows.
    
    Extends the built-in list type with M8-specific functionality.
    """
    
    def __init__(self):
        """Initialize a song matrix with empty rows.
        
        Creates a new song matrix with ROW_COUNT rows, all initialized as empty.
        Each row contains COL_COUNT columns set to EMPTY_CHAIN.
        """
        super().__init__()
        # Initialize with empty rows
        for _ in range(ROW_COUNT):
            self.append(M8SongRow())
    
    @classmethod
    def read(cls, data):
        """Create a song matrix from binary data.
        
        Parses the binary representation of a song matrix from an M8 file,
        constructing the row structure based on the fixed layout.
        
        Args:
            data (bytes): Binary data containing song rows, with each row
                        taking up COL_COUNT bytes
            
        Returns:
            M8SongMatrix: New instance with rows initialized from the binary data
        """
        instance = cls.__new__(cls)  # Create instance without calling __init__
        list.__init__(instance)  # Initialize the list properly
        
        for i in range(ROW_COUNT):
            start = i * COL_COUNT
            row_data = data[start:start + COL_COUNT]
            instance.append(M8SongRow.read(row_data))
        
        return instance
    
    def clone(self):
        """Create a deep copy of this song matrix.
        
        Creates an entirely new instance with all rows copied, rather than just
        a shallow reference copy.
        
        Returns:
            M8SongMatrix: New instance with cloned rows
        """
        instance = self.__class__()
        instance.clear()  # Remove default items
        
        for row in self:
            instance.append(row.clone())
        
        return instance
    
    def is_empty(self):
        """Check if this song matrix is empty (all rows are empty).
        
        A song matrix is considered empty if all rows are empty
        (i.e., no chains are referenced anywhere in the matrix).
        
        Returns:
            bool: True if all rows are empty, False otherwise
        """
        return all(row.is_empty() for row in self)
    
    def write(self):
        """Convert the song matrix to binary data.
        
        Serializes the entire song matrix to its binary representation
        for saving to an M8 project file. Each row takes up COL_COUNT bytes.
        
        Returns:
            bytes: Binary representation of the song matrix
        """
        result = bytearray()
        for row in self:
            row_data = row.write()
            result.extend(row_data)
        return bytes(result)
    
    def validate_chains(self, chains):
        """Validate that all rows reference valid chains.
        
        Checks the entire song matrix to ensure all referenced chains exist
        and are not empty. This helps maintain data integrity in the project.
        
        Args:
            chains (list): List of M8Chain objects to validate against
            
        Raises:
            M8ValidationError: If any row references a non-existent or empty chain,
                             with details about which row contains the invalid reference
        """
        for row_idx, row in enumerate(self):
            try:
                row.validate_chains(chains)
            except M8ValidationError as e:
                raise M8ValidationError(f"Row {row_idx}: {str(e)}") from e
    
    def as_list(self):
        """Convert song matrix to list for serialization.
        
        Creates a sparse representation of the song matrix for more efficient
        storage in formats like JSON. Only non-empty rows are included, each
        with their position index to preserve placement.
        
        Returns:
            list: List of dictionaries representing rows, with each dictionary
                containing the row data and its index in the matrix
        """
        # Only include non-empty rows
        result = []
        for i, row in enumerate(self):
            if not row.is_empty():
                row_dict = row.as_dict()
                row_dict["index"] = i
                result.append(row_dict)
        
        return result
    
    @classmethod
    def from_list(cls, items):
        """Create a song matrix from a list of dictionaries.
        
        Deserializes a song matrix from a sparse representation, typically
        created by the as_list() method or loaded from JSON. Reconstructs
        the full matrix by placing rows at their original indices.
        
        Args:
            items (list): List of dictionaries with row data, each containing
                        an "index" key and row content (chain references)
            
        Returns:
            M8SongMatrix: New instance with rows positioned according to their
                        original indices in the song
        """
        instance = cls()
        
        # Set rows
        if items:
            for row_data in items:
                row_idx = row_data.get("index", 0)
                if 0 <= row_idx < ROW_COUNT:
                    instance[row_idx] = M8SongRow.from_dict(row_data)
        
        return instance
