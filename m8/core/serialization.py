# In m8/core/serialization.py
import json
import importlib

# Cache to track objects being deserialized to prevent circular references
_deserialize_cache = {}

def _get_class_from_string(class_path):
    """Load a class from its string representation"""
    module_name, class_name = class_path.rsplit('.', 1)
    module = importlib.import_module(module_name)
    return getattr(module, class_name)

def to_json(obj, indent=None):
    """Convert any M8 object to JSON string"""
    return json.dumps(obj, indent=indent, default=_json_serializer)

def _json_serializer(obj):
    """Default serializer for custom M8 types"""
    # If the object has an as_dict method, use it
    if hasattr(obj, "as_dict"):
        return obj.as_dict()
    
    # If the object is a list or has as_list method
    if hasattr(obj, "as_list"):
        data = {"__list__": obj.as_list()}
        data["__class__"] = f"{obj.__class__.__module__}.{obj.__class__.__name__}"
        return data
    
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

def from_json(json_str, target_class=None):
    """Deserialize JSON string to an object
    
    If target_class is provided, the JSON is deserialized to that class.
    Otherwise, the class is determined from the JSON data if possible.
    """
    global _deserialize_cache
    _deserialize_cache = {}  # Reset cache for new deserialization
    return json.loads(json_str, object_hook=lambda d: _json_deserializer(d, target_class))

def _json_deserializer(obj, target_class=None):
    # Add this at the beginning of the function
    if isinstance(obj, dict) and "__class__" in obj:
        class_name = obj["__class__"]
        if "phrases" in obj and not isinstance(obj["phrases"], dict):
            print(f"Found non-dict phrases in {class_name}: {type(obj['phrases'])}")
            # If phrases is an M8Project, we've found our issue
            if hasattr(obj["phrases"], "__class__") and obj["phrases"].__class__.__name__ == "M8Project":
                print("*** CIRCULAR REFERENCE DETECTED: phrases is an M8Project ***")
                # Convert back to a dict if possible
                if hasattr(obj["phrases"], "as_dict"):
                    obj["phrases"] = obj["phrases"].as_dict()
                    print("Converted phrases back to a dictionary")
    
    # Rest of your function
    """Custom JSON object hook for deserializing M8 objects"""
    # Handle object with explicit class
    if isinstance(obj, dict) and "__class__" in obj:
        cls_path = obj.pop("__class__")
        
        # Create a cache key based on the object content and class
        # This helps identify the same logical object being deserialized multiple times
        cache_key = (cls_path, str(sorted(obj.items())) if len(obj) < 100 else id(obj))
        
        # Check if we're already deserializing this object
        if cache_key in _deserialize_cache:
            return _deserialize_cache[cache_key]
        
        # If target_class is specified, use it instead of the stored class
        cls = target_class if target_class else _get_class_from_string(cls_path)
        
        # Create a placeholder in the cache to break circular references
        # Just use an empty instance for now
        if hasattr(cls, "__new__"):
            _deserialize_cache[cache_key] = cls.__new__(cls)
        
        # Handle list types
        if "__list__" in obj:
            items = obj.pop("__list__")
            
            # Process items to handle any that might already be deserialized objects
            processed_items = []
            for item in items:
                if isinstance(item, object) and hasattr(item, '__class__') and not isinstance(item, (dict, list)):
                    # This is already a deserialized object, not a dictionary
                    if hasattr(item, 'as_dict'):
                        # Convert back to a dictionary
                        processed_items.append(item.as_dict())
                    else:
                        # Can't convert, just use as is
                        processed_items.append(item)
                else:
                    processed_items.append(item)
            
            result = cls.from_list(processed_items) if hasattr(cls, "from_list") else cls(items=processed_items)
            _deserialize_cache[cache_key] = result
            return result
            
        # Handle regular objects
        result = cls.from_dict(obj) if hasattr(cls, "from_dict") else cls(**obj)
        _deserialize_cache[cache_key] = result
        return result
        
    return obj
