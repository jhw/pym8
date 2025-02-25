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
