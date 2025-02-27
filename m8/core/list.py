from m8 import M8Block, NULL
from m8.core import auto_name_decorator, set_caller_module_decorator

import struct

class M8List(list):
    def __init__(self, items=None):
        super().__init__()

        if not hasattr(self.__class__, "ROW_CLASS"):
            raise AttributeError(f"{self.__class__.__name__} must define ROW_CLASS")

        # Initialize with empty rows or provided items
        if items is None:
            # Default initialization with empty rows
            for _ in range(self.ROW_COUNT):
                self.append(self.ROW_CLASS())
        else:
            # Initialize with provided items
            if len(items) > self.ROW_COUNT:
                raise ValueError(f"Too many items: got {len(items)}, max is {self.ROW_COUNT}")
            
            # Add provided items
            for item in items:
                self.append(item)
            
            # Fill remaining slots with empty rows
            remaining = self.ROW_COUNT - len(items)
            for _ in range(remaining):
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
        """Convert list to list of dictionaries for serialization"""
        result = []
        for item in self:
            if hasattr(item, "as_dict"):
                result.append(item.as_dict())
            elif hasattr(item, "as_list"):
                result.append({"__list__": item.as_list(), "__class__": f"{item.__class__.__module__}.{item.__class__.__name__}"})
            else:
                # For simple types or M8Blocks
                result.append(None)  # Use None for empty items
        return result

    def as_dict(self):
        """Convert list to dictionary for serialization"""
        return {
            "__class__": f"{self.__class__.__module__}.{self.__class__.__name__}",
            "items": self.as_list()
        }

    def write(self):
        result = bytearray()
        for row in self:
            row_data = row.write()
            # Ensure each row occupies exactly ROW_SIZE bytes
            if len(row_data) < self.ROW_SIZE:
                # Pad with the default byte if the row data is shorter than expected
                default_byte = getattr(self, "DEFAULT_BYTE", NULL)  # Default to NULL if not defined
                row_data = row_data + bytes([default_byte] * (self.ROW_SIZE - len(row_data)))
            elif len(row_data) > self.ROW_SIZE:
                # Truncate if the row data is longer than expected
                row_data = row_data[:self.ROW_SIZE]
            result.extend(row_data)
        return bytes(result)
    
    @classmethod
    def from_list(cls, items):
        """Create an instance from a list of items"""
        instance = cls()
        
        for i, item_data in enumerate(items):
            if i < len(instance) and item_data is not None:
                # Determine class for this item
                row_class = cls.ROW_CLASS
                
                # If the class has a resolver, use it if there's class info
                if hasattr(cls, "ROW_CLASS_RESOLVER") and isinstance(item_data, dict) and "__class__" in item_data:
                    class_path = item_data["__class__"]
                    from m8.core.serialization import _get_class_from_string
                    row_class = _get_class_from_string(class_path)
                    
                # Create the item
                if hasattr(row_class, "from_dict"):
                    instance[i] = row_class.from_dict(item_data)
                elif hasattr(row_class, "from_list") and "__list__" in item_data:
                    instance[i] = row_class.from_list(item_data["__list__"])
        
        return instance

    @classmethod
    def from_dict(cls, data):
        """Create an instance from a dictionary"""
        if "items" in data:
            return cls.from_list(data["items"])
        return cls()

    def to_json(self, indent=None):
        """Convert list to JSON string"""
        from m8.core.serialization import to_json
        return to_json(self, indent=indent)

    @classmethod
    def from_json(cls, json_str):
        """Create an instance from a JSON string"""
        from m8.core.serialization import from_json
        return from_json(json_str, cls)

@set_caller_module_decorator
@auto_name_decorator
def m8_list_class(row_size, row_count, name=None, row_class=M8Block, row_class_resolver=None, default_byte=NULL):
    attributes = {
        "ROW_SIZE": row_size,
        "ROW_COUNT": row_count,
        "ROW_CLASS": row_class,
        "DEFAULT_BYTE": default_byte,  # Store the default byte for padding
    }

    if row_class_resolver:
        attributes["ROW_CLASS_RESOLVER"] = row_class_resolver

    return type(name, (M8List,), attributes)
