NULL, BLANK = 0x00, 0xFF

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
