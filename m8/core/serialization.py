import json
import importlib

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
    return json.loads(json_str, object_hook=lambda d: _json_deserializer(d, target_class))

def _json_deserializer(obj, target_class=None):
    """Custom JSON object hook for deserializing M8 objects"""
    # Handle object with explicit class
    if isinstance(obj, dict) and "__class__" in obj:
        cls_path = obj.pop("__class__")
        
        # If target_class is specified, use it instead of the stored class
        cls = target_class if target_class else _get_class_from_string(cls_path)
        
        # Handle list types
        if "__list__" in obj:
            items = obj.pop("__list__")
            return cls.from_list(items) if hasattr(cls, "from_list") else cls(items=items)
            
        # Handle regular objects
        return cls.from_dict(obj) if hasattr(cls, "from_dict") else cls(**obj)
        
    return obj
