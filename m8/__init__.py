NULL, BLANK = 0x00, 0xFF

def load_class(class_path):
    module_name, class_name = class_path.rsplit('.', 1)
    module = __import__(module_name, fromlist=[class_name])
    return getattr(module, class_name)

class M8Block:
    def __init__(self):
        self.data = bytearray()

    @classmethod
    def read(cls, data):
        instance = cls()
        instance.data = data
        return instance

    def is_empty(self):
        return all(b == NULL for b in self.data)
    
    def write(self):
        return self.data

class M8ValidationError(Exception):
    pass

class M8IndexError(IndexError):
    pass
