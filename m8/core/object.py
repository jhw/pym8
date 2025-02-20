from m8 import M8Block, NULL
from m8.core import m8_class_name
from m8.utils.bits import split_byte, join_nibbles

import struct

FORMAT_MAP = {
    "UINT8": "B",
    "UINT4_2": "B",  # Single byte interpreted as two 4-bit values
    "FLOAT32": "<f",
    "STRING": "{}s"  # Takes size from options
}

class M8Object:
    def __init__(self, **kwargs):
        self._data = bytearray(self.DEFAULT_DATA)

        # Validate all kwargs are valid field names
        for name in kwargs:
            if not self._get_field_parts(name):
                raise AttributeError(f"Field '{name}' not found in {self.__class__.__name__}")

        # Process each requested field
        for name, value in kwargs.items():
            if value is not None:
                setattr(self, name, value)

        # Set defaults for any fields not in kwargs
        for field_name, field in self.FIELD_MAP.items():
            if field["format"] == "UINT4_2":
                names = field_name.split("|")
                default = field.get("default", 0)
                upper, lower = split_byte(default)
                
                # Handle each part separately
                if names[0] != "_" and names[0] not in kwargs:
                    setattr(self, names[0], upper)
                if names[1] != "_" and names[1] not in kwargs:
                    setattr(self, names[1], lower)
            elif field_name not in kwargs:
                value = field.get("default", None)
                if value is not None:
                    setattr(self, field_name, value)

    @classmethod
    def read(cls, data):
        # Calculate required length from field map
        required_length = max(field["end"] for field in cls.FIELD_MAP.values())
        
        if len(data) < required_length:
            raise ValueError(f"Data too short: got {len(data)} bytes, need {required_length}")
            
        instance = cls()
        instance._data = bytearray(data)
        return instance
                    
    def clone(self):
        return self.__class__.read(bytes(self._data))

    def _get_field_parts(self, name):
        """Returns (field_name, field, part_index) for any field containing this name"""
        # Direct field match
        if name in self.FIELD_MAP:
            return [(name, self.FIELD_MAP[name], None)]
        
        # Look for composite fields containing this name
        matches = []
        for field_name, field in self.FIELD_MAP.items():
            if field["format"] == "UINT4_2":
                names = field_name.split("|")
                if name in names:
                    idx = names.index(name)
                    matches.append((field_name, field, idx))
        return matches

    def _get_field(self, field_name):
        matches = self._get_field_parts(field_name)
        if not matches:
            raise AttributeError(f"Field '{field_name}' not found in {self.__class__.__name__}")
        return matches[0][1]  # Return the field definition

    def _get_field_format(self, field):
        base_format = FORMAT_MAP[field["format"]]
        if field["format"] == "STRING":
            return base_format.format(field["end"] - field["start"])
        return base_format

    def get_int(self, field_name):
        matches = self._get_field_parts(field_name)
        if not matches:
            raise AttributeError(f"Field '{field_name}' not found in {self.__class__.__name__}")
        
        field_name, field, idx = matches[0]
        raw_value = struct.unpack(self._get_field_format(field), 
                                self._data[field["start"]:field["end"]])[0]

        # Extract part value if this is a composite field
        if idx is not None and field["format"] == "UINT4_2":
            upper, lower = split_byte(raw_value)
            return lower if idx == 1 else upper

        return raw_value

    def get_float(self, field_name):
        return self._get_value(field_name, float)

    def get_string(self, field_name, encoding="utf-8"):
        field = self._get_field(field_name)
        return self._data[field["start"]:field["end"]].split(b'\x00', 1)[0].decode(encoding, errors='ignore')

    def set_int(self, field_name, value):
        matches = self._get_field_parts(field_name)
        if not matches:
            raise AttributeError(f"Field '{field_name}' not found in {self.__class__.__name__}")
        
        field_name, field, idx = matches[0]
        value = int(value)

        if idx is not None and field["format"] == "UINT4_2":
            current = struct.unpack(FORMAT_MAP[field["format"]], 
                                  self._data[field["start"]:field["end"]])[0]
            current_upper, current_lower = split_byte(current)
            
            # Set either upper or lower nibble while preserving the other
            if idx == 0:  # First name, set upper bits
                new_value = join_nibbles(value, current_lower)
            else:  # Second name, set lower bits
                new_value = join_nibbles(current_upper, value)
                
            self._data[field["start"]:field["end"]] = struct.pack(FORMAT_MAP[field["format"]], 
                                                                 new_value)
        else:
            # Regular field
            self._data[field["start"]:field["end"]] = struct.pack(self._get_field_format(field), 
                                                                 value)

    def set_float(self, field_name, value):
        self._set_value(field_name, value, float)

    def set_string(self, field_name, value, encoding="utf-8"):
        field = self._get_field(field_name)
        field_size = field["end"] - field["start"]
        
        # Encode and either trim or pad with spaces
        encoded = value.encode(encoding)
        if len(encoded) > field_size:
            encoded = encoded[:field_size]
        else:
            encoded = encoded.ljust(field_size, b' ')
            
        self._data[field["start"]:field["end"]] = encoded

    def _get_value(self, field_name, value_type):
        field = self._get_field(field_name)
        return value_type(struct.unpack(self._get_field_format(field), 
                                      self._data[field["start"]:field["end"]])[0])

    def _set_value(self, field_name, value, value_type):
        field = self._get_field(field_name)
        self._data[field["start"]:field["end"]] = struct.pack(self._get_field_format(field), 
                                                             value_type(value))

    def __getattr__(self, name):
        field = self._get_field(name)
        if field["format"] == "STRING":
            return self.get_string(name)
        elif field["format"] == "FLOAT32":
            return self.get_float(name)
        else:
            return self.get_int(name)

    def __setattr__(self, name, value):
        if "_data" in self.__dict__:
            try:
                field = self._get_field(name)
                if field["format"] == "STRING":
                    self.set_string(name, value)
                elif field["format"] == "FLOAT32":
                    self.set_float(name, value)
                else:
                    self.set_int(name, value)
            except AttributeError:
                object.__setattr__(self, name, value)
        else:
            object.__setattr__(self, name, value)

    def as_dict(self):
        result = {}
    
        # Handle all field parts
        for field_name, field in self.FIELD_MAP.items():
            if field["format"] == "UINT4_2":
                for name in field_name.split("|"):
                    if name != "_":
                        result[name] = self.get_int(name)
            elif field["format"] == "STRING":
                result[field_name] = self.get_string(field_name)
            elif field["format"] == "FLOAT32":
                result[field_name] = self.get_float(field_name)
            else:
                result[field_name] = self.get_int(field_name)
                
        return result
            
    def write(self):
        return bytes(self._data)

def expand_field_map(field_map):
    expanded = {}
    for field in field_map:
        name, default, start, end, fmt = field
        expanded[name] = {
            "name": name,
            "default": default,
            "start": start,
            "end": end,
            "format": fmt
        }
    return expanded

def m8_object_class(field_map, block_sz=None, block_byte=NULL, block_head_byte=NULL):
    name = m8_class_name("M8Object")
    field_map = expand_field_map(field_map)  # Convert list to dictionary

    # Validate formats
    invalid_formats = [
        f"{field_name}: {field['format']}" 
        for field_name, field in field_map.items() 
        if field["format"] not in FORMAT_MAP
    ]
    if invalid_formats:
        raise ValueError(f"Invalid format(s) in {name}: {', '.join(invalid_formats)}")

    if block_sz is None:
        block_sz = max(field["end"] for field in field_map.values())

    default_data = bytearray([block_byte] * block_sz)
    default_data[0] = block_head_byte

    return type(name, (M8Object,), {
        "FIELD_MAP": field_map,
        "DEFAULT_DATA": bytes(default_data),
    })
