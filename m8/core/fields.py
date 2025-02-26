from m8 import NULL
from m8.utils.bits import split_byte, join_nibbles

import struct

# Format map for field types
FORMAT_MAP = {
    "UINT8": "B",
    "UINT4_2": "B",  # Single byte interpreted as two 4-bit values
    "FLOAT32": "<f",
    "STRING": "{}s"  # Takes size from options
}

class M8Field:
    """Represents a single field in an M8 object"""
    def __init__(self, name, default, start, end, format_type):
        self.name = name
        self.default = default
        self.start = start
        self.end = end
        self.format = format_type
        
        # Validate format
        if format_type not in FORMAT_MAP:
            raise ValueError(f"Invalid format '{format_type}' for field '{name}'")
            
        # For UINT4_2 fields, parse the composite names
        self.is_composite = format_type == "UINT4_2" and "|" in name
        self.parts = name.split("|") if self.is_composite else [name]
    
    def get_format_string(self):
        """Returns the struct format string for this field"""
        base_format = FORMAT_MAP[self.format]
        if self.format == "STRING":
            return base_format.format(self.end - self.start)
        return base_format
        
    def get_part_name(self, part_index):
        """Get the name of a specific part for composite fields"""
        if not self.is_composite:
            return self.name
            
        return self.parts[part_index]
        
    def is_empty_part(self, part_index):
        """Check if a part name is a placeholder (_)"""
        return self.parts[part_index] == "_"
    
    def read_value(self, data, part_index=None):
        """Read raw value from data"""
        raw_value = struct.unpack(self.get_format_string(), 
                              data[self.start:self.end])[0]
        
        if part_index is not None and self.is_composite:
            upper, lower = split_byte(raw_value)
            return lower if part_index == 1 else upper
            
        return raw_value
        
    def write_value(self, data, value, part_index=None):
        """Write value to data"""
        if part_index is not None and self.is_composite:
            current = struct.unpack(self.get_format_string(), 
                                data[self.start:self.end])[0]
            upper, lower = split_byte(current)
            
            if part_index == 0:
                new_value = join_nibbles(int(value), lower)
            else:
                new_value = join_nibbles(upper, int(value))
                
            data[self.start:self.end] = struct.pack(self.get_format_string(), new_value)
        else:
            data[self.start:self.end] = struct.pack(self.get_format_string(), value)
        
    def get_typed_value(self, data, part_index=None):
        """Get value with proper type (string, float, int)"""
        if self.format == "STRING":
            return data[self.start:self.end].split(b'\x00', 1)[0].decode('utf-8', errors='ignore')
        elif self.format == "FLOAT32":
            return struct.unpack("<f", data[self.start:self.end])[0]
        else:
            return self.read_value(data, part_index)
    
    def set_typed_value(self, data, value, part_index=None):
        """Set value with proper type handling"""
        if self.format == "STRING":
            # Encode and either trim or pad with nulls
            encoded = value.encode('utf-8')
            field_size = self.end - self.start
            
            if len(encoded) > field_size:
                encoded = encoded[:field_size]
            else:
                encoded = encoded.ljust(field_size, b'\x00')
                
            data[self.start:self.end] = encoded
        elif self.format == "FLOAT32":
            data[self.start:self.end] = struct.pack("<f", float(value))
        else:
            # Convert to integer
            self.write_value(data, int(value), part_index)
    
    def check_default(self, data, part_index=None):
        """Check if the field has its default value in the given data"""
        if self.format == "STRING":
            current = self.get_typed_value(data)
            return current.rstrip() == str(self.default).rstrip()
        elif self.format == "FLOAT32":
            current = self.get_typed_value(data)
            return abs(current - float(self.default)) < 1e-6
        else:
            current = self.read_value(data, part_index)
            
            if self.is_composite and part_index is not None:
                # For composite fields, extract the appropriate default nibble
                default_value = self.default
                default_upper, default_lower = split_byte(default_value)
                expected = default_lower if part_index == 1 else default_upper
                return current == expected
            
            return current == int(self.default)

    def serialize_value(self, value):
        """Convert a value to a serializable form based on field type"""
        # For JSON serialization, just return the value as is
        return value
        
    def deserialize_value(self, value):
        """Convert a serialized value back to the appropriate type"""
        if self.format == "FLOAT32":
            return float(value)
        elif self.format in ["UINT8", "UINT4_2"]:
            return int(value)
        return value


class M8FieldMap:
    """Manages field definitions for M8 objects"""
    def __init__(self, field_defs):
        self.fields = {}
        self.part_map = {}  # Maps part names to field names and indices
        
        # Process field definitions
        for field_def in field_defs:
            # Handle the original list format from client code
            name, default, start, end, fmt = field_def[:5]
                
            # Create field object
            field = M8Field(name, default, start, end, fmt)
            self.fields[name] = field
            
            # Register part names for lookup
            if field.is_composite:
                for i, part_name in enumerate(field.parts):
                    if part_name != "_":  # Skip placeholder parts
                        self.part_map[part_name] = (name, i)
    
    def get_field(self, name):
        """Get field by name, returns (field, part_index)"""
        if name in self.fields:
            return self.fields[name], None
            
        if name in self.part_map:
            field_name, part_index = self.part_map[name]
            return self.fields[field_name], part_index
            
        raise AttributeError(f"Field '{name}' not found in field map")
    
    def has_field(self, name):
        """Check if field exists"""
        return name in self.fields or name in self.part_map
    
    def max_offset(self):
        """Get the maximum byte offset needed"""
        return max(field.end for field in self.fields.values())
    
    def get_default_byte_at(self, offset):
        """Get the default byte value for a specific offset"""
        for field in self.fields.values():
            if field.start <= offset < field.end:
                if field.format == "STRING" and isinstance(field.default, str):
                    # For strings, encode and get the byte at the relative position
                    str_bytes = field.default.encode('utf-8')
                    rel_offset = offset - field.start
                    if rel_offset < len(str_bytes):
                        return str_bytes[rel_offset]
                    return 0x00  # Null padding
                elif field.format == "FLOAT32":
                    # For floats, pack to bytes and get the appropriate byte
                    float_bytes = struct.pack("<f", field.default)
                    return float_bytes[offset - field.start]
                elif field.format == "UINT4_2" and offset == field.start:
                    # For composite fields, the default is directly usable
                    return field.default
                elif field.format == "UINT8" and offset == field.start:
                    # For single-byte fields, the default is directly usable
                    return field.default
                    
        return NULL  # Default to NULL for unspecified offsets
