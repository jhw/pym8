from m8 import M8Block, NULL
from m8.core import m8_class_name

import struct

class M8List(list):
    def __init__(self):
        super().__init__()

        if not hasattr(self.__class__, "ROW_CLASS"):
            raise AttributeError(f"{self.__class__.__name__} must define ROW_CLASS")

        for _ in range(self.ROW_COUNT):
            self.append(self.ROW_CLASS())
    
    @classmethod
    def read(cls, data):
        instance = cls()
        has_resolver = hasattr(cls, "ROW_CLASS_RESOLVER")
        
        for i in range(cls.ROW_COUNT):
            start = i * cls.ROW_SIZE
            row_data = data[start:start + cls.ROW_SIZE]

            row_class = cls.ROW_CLASS_RESOLVER(row_data) if has_resolver else cls.ROW_CLASS
            instance[i] = row_class.read(row_data)

        return instance

    def clone(self):
        instance = self.__class__()
        for i, row in enumerate(self):
            # Call clone() on row if it exists, otherwise create a new one
            if hasattr(row, 'clone'):
                instance[i] = row.clone()
            else:
                instance[i] = self.ROW_CLASS.read(row.write())
        return instance

    def is_empty(self):
        for row in self:
            if hasattr(row, 'is_empty'):
                if not row.is_empty():
                    return False
        return True
    
    def as_list(self):
        return [row.as_dict() for row in self if hasattr(row, "as_dict")]

    def write(self):
        return b"".join(row.write() for row in self)

def m8_list_class(row_size, row_count, row_class=M8Block, row_class_resolver=None):
    name = m8_class_name("M8List")
    attributes = {
        "ROW_SIZE": row_size,
        "ROW_COUNT": row_count,
        "ROW_CLASS": row_class,
    }

    if row_class_resolver:
        attributes["ROW_CLASS_RESOLVER"] = row_class_resolver

    return type(name, (M8List,), attributes)


