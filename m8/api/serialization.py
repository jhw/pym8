import json
from m8.api import load_class

def to_json(obj, indent=None):
    """Simple serialization to JSON for M8 objects"""
    if hasattr(obj, 'as_dict'):
        return json.dumps(obj.as_dict(), indent=indent)
    elif isinstance(obj, list):
        # Handle list serialization
        return json.dumps([item.as_dict() if hasattr(item, 'as_dict') else item for item in obj], indent=indent)
    else:
        # For primitive types
        return json.dumps(obj, indent=indent)

def from_json(json_str, cls=None):
    """Simple deserialization from JSON for M8 objects"""
    data = json.loads(json_str)
    
    # If no class specified, just return the data
    if cls is None:
        return data
    
    # Handle direct class instantiation if we have class info
    if isinstance(data, dict) and "__class__" in data:
        class_path = data["__class__"]
        # If the target class is already provided, use it
        if cls.__module__ + '.' + cls.__name__ == class_path:
            return cls.from_dict(data)
        
        # Otherwise, try to load the class from the path
        try:
            target_cls = load_class(class_path)
            return target_cls.from_dict(data)
        except (ImportError, AttributeError):
            # Fall back to the provided class if loading fails
            return cls.from_dict(data)
    
    # For lists or other types, use the class's from_dict if available
    if hasattr(cls, 'from_dict'):
        return cls.from_dict(data)
    
    # Just return the data as is if we can't deserialize
    return data
