"""JSON serialization utilities for M8 data."""

import json

class M8JSONEncoder(json.JSONEncoder):
    """Custom JSON encoder that converts small integers (0-255) to hex strings."""
    
    def iterencode(self, obj, _one_shot=False):
        # Pre-process the object to convert all integers to hex strings
        obj = self._process_object(obj)
        return super().iterencode(obj, _one_shot)
    
    def _process_object(self, obj):
        if isinstance(obj, int) and obj < 256:
            # Convert integers to hex strings with '0x' prefix
            return f"0x{obj:02x}"
        elif isinstance(obj, dict):
            # Process dictionaries recursively
            return {k: self._process_object(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            # Process lists recursively
            return [self._process_object(item) for item in obj]
        else:
            # Return other types unchanged
            return obj

def m8_json_decoder(obj):
    """Convert hex strings back to integers in decoded JSON."""
    for key, value in obj.items():
        if isinstance(value, str) and value.startswith("0x"):
            try:
                # Convert hex strings back to integers
                obj[key] = int(value, 16)
            except ValueError:
                pass
    return obj

def json_dumps(obj, indent=2):
    """Serialize an object to JSON using M8 encoding (integers as hex strings)."""
    return json.dumps(obj,
                      indent=indent,
                      cls=M8JSONEncoder)

def json_loads(json_str):
    """Deserialize a JSON string using M8 decoding (hex strings to integers)."""
    return json.loads(json_str,
                     object_hook=m8_json_decoder)