from m8 import NULL
from m8.core import m8_class_name
from m8.core.fields import M8FieldMap

import struct

class M8Object:
    def __init__(self, **kwargs):
        self._data = bytearray(self.DEFAULT_DATA)

        # Validate all kwargs are valid field names
        for name in kwargs:
            if not self.FIELD_MAP.has_field(name):
                raise AttributeError(f"Field '{name}' not found in {self.__class__.__name__}")

        # Process each requested field
        for name, value in kwargs.items():
            if value is not None:
                setattr(self, name, value)

    @classmethod
    def read(cls, data):
        # Calculate required length from field map
        required_length = cls.FIELD_MAP.max_offset()
        
        if len(data) < required_length:
            raise ValueError(f"Data too short: got {len(data)} bytes, need {required_length}")
            
        instance = cls()
        instance._data = bytearray(data)
        return instance
                    
    def clone(self):
        return self.__class__.read(bytes(self._data))

    def get_int(self, field_name):
        field, part_index = self.FIELD_MAP.get_field(field_name)
        return field.read_value(self._data, part_index)

    def get_float(self, field_name):
        field, part_index = self.FIELD_MAP.get_field(field_name)
        return field.get_typed_value(self._data)

    def get_string(self, field_name, encoding="utf-8"):
        field, part_index = self.FIELD_MAP.get_field(field_name)
        return field.get_typed_value(self._data)

    def set_int(self, field_name, value):
        field, part_index = self.FIELD_MAP.get_field(field_name)
        field.write_value(self._data, int(value), part_index)
        
    def set_float(self, field_name, value):
        field, part_index = self.FIELD_MAP.get_field(field_name)
        field.set_typed_value(self._data, float(value))

    def set_string(self, field_name, value, encoding="utf-8"):
        field, part_index = self.FIELD_MAP.get_field(field_name)
        field.set_typed_value(self._data, value)

    def __getattr__(self, name):
        field, part_index = self.FIELD_MAP.get_field(name)
        return field.get_typed_value(self._data, part_index)

    def __setattr__(self, name, value):
        if "_data" in self.__dict__:
            try:
                field, part_index = self.FIELD_MAP.get_field(name)
                field.set_typed_value(self._data, value, part_index)
            except AttributeError:
                object.__setattr__(self, name, value)
        else:
            object.__setattr__(self, name, value)

    def as_dict(self):
        """Convert object to dict for serialization"""
        result = {}
        
        # Include class information
        result["__class__"] = f"{self.__class__.__module__}.{self.__class__.__name__}"
        
        # Handle all fields
        for field_name, field in self.FIELD_MAP.fields.items():
            if field.is_composite:
                # For composite fields, split into parts
                for i, part_name in enumerate(field.parts):
                    if part_name != "_":  # Skip placeholder parts
                        value = field.get_typed_value(self._data, i)
                        result[part_name] = value
            else:
                # For regular fields
                value = field.get_typed_value(self._data)
                result[field_name] = value
                        
        return result            
            
    def is_empty(self):
        """Return True if all fields match their default values"""
        for field_name, field in self.FIELD_MAP.fields.items():
            if field.is_composite:
                # Check each named part of composite fields
                for i, part_name in enumerate(field.parts):
                    if part_name != "_" and not field.check_default(self._data, i):
                        return False
            else:
                # Check regular fields
                if not field.check_default(self._data):
                    return False
        return True

    def write(self):
        return bytes(self._data)

    @classmethod
    def from_dict(cls, data):
        """Create an instance from a dictionary"""
        instance = cls()
        
        # Process each field in the data dictionary
        for key, value in data.items():
            if cls.FIELD_MAP.has_field(key):
                setattr(instance, key, value)
                
        return instance

    def to_json(self, indent=None):
        """Convert object to JSON string"""
        from m8.core.serialization import to_json
        return to_json(self, indent=indent)

    @classmethod
    def from_json(cls, json_str):
        """Create an instance from a JSON string"""
        from m8.core.serialization import from_json
        return from_json(json_str, cls)


def m8_object_class(field_map, block_sz=None, default_byte=NULL, block_head_byte=NULL):
    name = m8_class_name("M8Object")
    
    # Create field map directly from the client-provided field definitions
    field_map_obj = M8FieldMap(field_map)
    
    # Determine block size
    if block_sz is None:
        block_sz = field_map_obj.max_offset()

    # Create default data array with appropriate values
    default_data = bytearray([default_byte] * block_sz)
    default_data[0] = block_head_byte
    
    # Set default values for fields
    for i in range(block_sz):
        field_default = field_map_obj.get_default_byte_at(i)
        if field_default is not None:
            default_data[i] = field_default

    # Create the class
    return type(name, (M8Object,), {
        "FIELD_MAP": field_map_obj,
        "DEFAULT_DATA": bytes(default_data),
    })
