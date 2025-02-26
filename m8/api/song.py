from m8 import NULL
from m8.api import M8ValidationError, BLANK
from m8.core.array import m8_array_class
from m8.core.list import m8_list_class

COL_COUNT = 8
ROW_COUNT = 255

M8SongRowBase = m8_array_class(
    default_byte=BLANK,
    length=COL_COUNT,
    fmt="B"
)

class M8SongRow(M8SongRowBase):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

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
        from m8.core.serialization import to_json
        return to_json(self, indent=indent)

    @classmethod
    def from_json(cls, json_str):
        """Create an instance from a JSON string"""
        from m8.core.serialization import from_json
        return from_json(json_str, cls)

M8SongMatrixBase = m8_list_class(
    row_class=M8SongRow,
    row_size=COL_COUNT,
    row_count=ROW_COUNT
)

class M8SongMatrix(M8SongMatrixBase):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

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
        from m8.core.serialization import to_json
        return to_json(self, indent=indent)

    @classmethod
    def from_json(cls, json_str):
        """Create an instance from a JSON string"""
        from m8.core.serialization import from_json
        return from_json(json_str, cls)
