NULL = 0x00

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

    def as_dict(self):
        """Convert block to dictionary for serialization"""
        return {
            "__class__": f"{self.__class__.__module__}.{self.__class__.__name__}",
            "data": list(self.data)
        }
    
    @classmethod
    def from_dict(cls, data):
        """Create an instance from a dictionary"""
        instance = cls()
        if "data" in data:
            instance.data = bytearray(data["data"])
        return instance

    def to_json(self, indent=None):
        """Convert block to JSON string"""
        from m8.api.serialization import to_json
        return to_json(self, indent=indent)

    @classmethod
    def from_json(cls, json_str):
        """Create an instance from a JSON string"""
        from m8.api.serialization import from_json
        return from_json(json_str, cls)
