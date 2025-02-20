from m8.core import M8ValidationError
from m8.core.list import m8_list_class
from m8.core.object import m8_object_class

STEP_BLOCK_SIZE = 2
STEP_COUNT = 16
CHAIN_BLOCK_SIZE = STEP_COUNT * STEP_BLOCK_SIZE
CHAIN_COUNT = 255

M8ChainStepBase = m8_object_class(
    field_map=[
        ("phrase", 0xFF, 0, 1, "UINT8"),
        ("transpose", 0x00, 1, 2, "UINT8")
    ]
)

class M8ChainStep(M8ChainStepBase):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def is_empty(self):
        return (self.phrase == 0xFF and
                self.transpose == 0x00)

M8ChainBase = m8_list_class(
    row_class=M8ChainStep,
    row_size=STEP_BLOCK_SIZE,
    row_count=STEP_COUNT
)

class M8Chain(M8ChainBase):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def validate_phrases(self, phrases):
        if not self.is_empty():
            for step_idx, step in enumerate(self):
                if step.phrase != 0xFF and (
                    step.phrase >= len(phrases) or 
                    phrases[step.phrase].is_empty()
                ):
                    raise M8ValidationError(
                        f"Chain step {step_idx} references non-existent or empty "
                        f"phrase {step.phrase}"
                    )
        
M8ChainsBase = m8_list_class(
    row_class=M8Chain,
    row_size=CHAIN_BLOCK_SIZE,
    row_count=CHAIN_COUNT
)

class M8Chains(M8ChainsBase):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def validate_phrases(self, phrases):
        for chain_idx, chain in enumerate(self):
            try:
                chain.validate_phrases(phrases)
            except M8ValidationError as e:
                raise M8ValidationError(f"Chain {chain_idx}: {str(e)}") from e

