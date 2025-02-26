# In m8/core/serialization.py
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

