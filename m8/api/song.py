from m8 import NULL
from m8.api import M8ValidationError, BLANK
from m8.core.serialization import from_json, to_json

import struct

COL_COUNT = 8
ROW_COUNT = 255

class M8SongRow:
    def __init__(self, **kwargs):
        self._data = bytearray([BLANK] * COL_COUNT)
        
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
        return all(chain == BLANK for chain in self._data)
    
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
    
    def validate_chains(self, chains):
        if not self.is_empty():
            for col_idx in range(COL_COUNT):
                chain_idx = self[col_idx]
                if chain_idx != BLANK and (
                    chain_idx >= len(chains) or 
                    chains[chain_idx].is_empty()
                ):
                    raise M8ValidationError(
                        f"Column {col_idx} references non-existent or empty "
                        f"chain {chain_idx}"
                    )
    
    def as_dict(self):
        """Convert song row to dictionary for serialization"""
        # Only include non-blank chain references
        chains = []
        for i in range(COL_COUNT):
            if self[i] != BLANK:
                chains.append({"col": i, "chain": self[i]})
        
        return {
            "__class__": f"{self.__class__.__module__}.{self.__class__.__name__}",
            "chains": chains
        }
    
    @classmethod
    def from_dict(cls, data):
        """Create a song row from a dictionary"""
        instance = cls()
        
        # Set chain references
        if "chains" in data:
            for chain_ref in data["chains"]:
                col = chain_ref.get("col", 0)
                chain = chain_ref.get("chain", BLANK)
                if 0 <= col < COL_COUNT:
                    instance[col] = chain
        
        return instance
    
    def to_json(self, indent=None):
        """Convert song row to JSON string"""
        return to_json(self, indent=indent)

    @classmethod
    def from_json(cls, json_str):
        """Create an instance from a JSON string"""
        return from_json(json_str, cls)


class M8SongMatrix(list):
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
        return all(row.is_empty() for row in self)
    
    def write(self):
        result = bytearray()
        for row in self:
            row_data = row.write()
            result.extend(row_data)
        return bytes(result)
    
    def validate_chains(self, chains):
        for row_idx, row in enumerate(self):
            try:
                row.validate_chains(chains)
            except M8ValidationError as e:
                raise M8ValidationError(f"Row {row_idx}: {str(e)}") from e
    
    def as_dict(self):
        """Convert song matrix to dictionary for serialization"""
        # Only include non-empty rows
        rows = []
        for i, row in enumerate(self):
            if not row.is_empty():
                row_dict = row.as_dict()
                row_dict["row"] = i
                rows.append(row_dict)
        
        return {
            "__class__": f"{self.__class__.__module__}.{self.__class__.__name__}",
            "rows": rows
        }
    
    @classmethod
    def from_dict(cls, data):
        """Create a song matrix from a dictionary"""
        instance = cls()
        
        # Set rows
        if "rows" in data:
            for row_data in data["rows"]:
                row_idx = row_data.get("row", 0)
                if 0 <= row_idx < ROW_COUNT:
                    instance[row_idx] = M8SongRow.from_dict(row_data)
        
        return instance
    
    def to_json(self, indent=None):
        """Convert song matrix to JSON string"""
        return to_json(self, indent=indent)

    @classmethod
    def from_json(cls, json_str):
        """Create an instance from a JSON string"""
        return from_json(json_str, cls)
