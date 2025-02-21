from m8 import M8ValidationError, M8Block, NULL, BLANK
from m8.core.list import m8_list_class
from m8.core.object import m8_object_class

FX_BLOCK_SIZE = 2
FX_BLOCK_COUNT = 3
STEP_BLOCK_SIZE = 9
STEP_COUNT = 16
PHRASE_BLOCK_SIZE = STEP_COUNT * STEP_BLOCK_SIZE
PHRASE_COUNT = 255

M8FXTuple = m8_object_class(
    field_map=[
        ("key", BLANK, 0, 1, "UINT8"),
        ("value", NULL, 1, 2, "UINT8")
    ]
)

M8FXTuples = m8_list_class(
    row_class=M8FXTuple,
    row_size=FX_BLOCK_SIZE,
    row_count=FX_BLOCK_COUNT
)

M8PhraseStepBase = m8_object_class(
    field_map=[
        ("note", BLANK, 0, 1, "UINT8"),
        ("velocity", BLANK, 1, 2, "UINT8"),
        ("instrument", BLANK, 2, 3, "UINT8")
    ]
)

class M8PhraseStep(M8PhraseStepBase):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.fx = M8FXTuples()

    @classmethod
    def read(cls, data):
        instance = cls()
        instance._data = bytearray(data[:3])
        instance.fx = M8FXTuples.read(data[3:])
        return instance

    def clone(self):
        instance = self.__class__()
        instance._data = bytearray(self._data)  # Clone base data
        instance.fx = self.fx.clone()  # Clone fx tuples
        return instance

    def is_empty(self):
        return (self.note == BLANK and
                self.velocity == BLANK and
                self.instrument == BLANK and
                self.fx.is_empty())

    @property
    def available_slot(self):
        for slot_idx, fx in enumerate(self.fx):
            if fx.is_empty() or (fx.key == BLANK):
                return slot_idx
        return None
    
    def add_fx(self, key, value):
        slot = self.available_slot
        if slot is None:
            raise M8IndexError("No empty FX slots available in this step")
            
        self.fx[slot] = M8FXTuple(key=key, value=value)
        return slot
        
    def set_fx(self, key, value, slot):
        if not (0 <= slot < FX_BLOCK_COUNT):
            raise M8IndexError(f"FX slot index must be between 0 and {FX_BLOCK_COUNT-1}")
            
        self.fx[slot] = M8FXTuple(key=key, value=value)    

    def as_dict(self):
        base_dict = super().as_dict()
        base_dict["fx"] = [fx.as_dict() for fx in self.fx if not fx.is_empty()]
        return base_dict
    
    def write(self):
        buffer = bytearray(super().write())
        buffer.extend(self.fx.write())
        return bytes(buffer)
        
M8PhraseBase = m8_list_class(
    row_class=M8PhraseStep,
    row_size=STEP_BLOCK_SIZE,
    row_count=STEP_COUNT
)

class M8Phrase(M8PhraseBase):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def validate_instruments(self, instruments):
        if not self.is_empty():
            for step_idx, step in enumerate(self):
                if step.instrument != BLANK and (
                    step.instrument >= len(instruments) or
                    isinstance(instruments[step.instrument], M8Block)
                ):
                    raise M8ValidationError(
                        f"Step {step_idx} references non-existent or empty "
                        f"instrument {step.instrument}"
                    )
        
M8PhrasesBase = m8_list_class(
    row_class=M8Phrase,
    row_size=PHRASE_BLOCK_SIZE,
    row_count=PHRASE_COUNT
)

class M8Phrases(M8PhrasesBase):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def validate_instruments(self, instruments):
        for phrase_idx, phrase in enumerate(self):
            try:
                phrase.validate_instruments(instruments)
            except M8ValidationError as e:
                raise M8ValidationError(f"Phrase {phrase_idx}: {str(e)}") from e

