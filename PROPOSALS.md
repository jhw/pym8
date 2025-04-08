# M8 Library Enhancement Proposals

## Enum String Parameter Support via Decorator (04/08/2025)

### Problem Statement

Currently, the M8 library has implemented enum support for serialization/deserialization and constructor arguments, but there are still gaps in API methods that accept parameter values that should support enum strings. Specifically, several key methods in `M8PhraseStep` for working with FX only accept numeric keys, not the more human-readable enum string values.

Examples include:
- `M8PhraseStep.add_fx(key, value)` 
- `M8PhraseStep.set_fx(key, value, slot)`
- `M8PhraseStep.get_fx(key)`
- `M8PhraseStep.delete_fx(key)`

These methods require numeric key values, forcing users to know and use the underlying numeric representations instead of the more intuitive enum strings.

### Proposed Solution

Implement a decorator in `m8/core/enums.py` that handles automatic conversion of string enum parameters to their numeric values. This would allow these methods to accept either numeric values or string enum names.

#### Decorator Implementation

```python
def with_enum_param(param_index=0, instrument_attr='instrument', empty_value=0xFF):
    """
    Decorator to convert string enum parameters to numeric values.
    
    Args:
        param_index: Index of the parameter to convert (default is 0, the first parameter)
        instrument_attr: Name of the attribute containing the instrument ID (default is 'instrument')
        empty_value: Value that represents an empty/invalid reference (default is 0xFF)
        
    Usage:
        @with_enum_param(param_index=0)  # Convert the first parameter (key)
        def add_fx(self, key, value):
            # key will be converted from string enum to numeric value if needed
            ...
    """
    def decorator(func):
        import functools
        
        @functools.wraps(func)
        def wrapper(self, *args, **kwargs):
            # Convert args to list to allow modification
            args_list = list(args)
            
            # Get the parameter to convert
            if len(args_list) > param_index:
                param = args_list[param_index]
                
                # Only convert if it's a string
                if isinstance(param, str):
                    # Get instrument ID from self
                    instrument_id = getattr(self, instrument_attr, empty_value)
                    
                    # Only proceed if we have a valid instrument reference
                    if instrument_id != empty_value:
                        context = M8InstrumentContext.get_instance()
                        
                        # Use context to find appropriate enum for this instrument type
                        with context.with_referenced_context(instrument_id):
                            # Get enum classes from configuration
                            from m8.config import get_fx_keys_enum_paths
                            instrument_type_id = context.get_instrument_type_id()
                            
                            if instrument_type_id is not None:
                                # Get enum paths for this instrument type
                                enum_paths = get_fx_keys_enum_paths(instrument_type_id)
                                
                                # Load enum classes
                                enum_classes = load_enum_classes(enum_paths)
                                
                                # Try each enum class to find the key
                                for enum_class in enum_classes:
                                    try:
                                        args_list[param_index] = enum_class[param].value
                                        break
                                    except KeyError:
                                        continue
            
            # Call the original function with possibly modified args
            return func(self, *args_list, **kwargs)
        
        return wrapper
    
    return decorator
```

#### Application

```python
from m8.core.enums import with_enum_param

class M8PhraseStep:
    # ...
    
    @with_enum_param(param_index=0)
    def add_fx(self, key, value):
        # Implementation remains unchanged - key is now guaranteed to be numeric
        existing_slot = self.find_fx_slot(key)
        # rest of function...
    
    @with_enum_param(param_index=0)
    def set_fx(self, key, value, slot):
        # Implementation remains unchanged
        # ...
```

#### Configuration Support

Add a utility function to `m8/config.py` to retrieve FX key enum paths:

```python
def get_fx_keys_enum_paths(instrument_type_id):
    """Get enum paths for FX keys for the given instrument type."""
    config = load_format_config()
    fx_enums = config.get("fx", {}).get("enums", {})
    
    # Try direct lookup by ID
    if instrument_type_id in fx_enums:
        return fx_enums[instrument_type_id]
    
    # Try hex format
    hex_key = f"0x{instrument_type_id:02x}"
    if hex_key in fx_enums:
        return fx_enums[hex_key]
    
    # Try string instrument type
    instrument_types = get_instrument_types()
    if instrument_type_id in instrument_types:
        instrument_type = instrument_types[instrument_type_id]
        if instrument_type in fx_enums:
            return fx_enums[instrument_type]
    
    return fx_enums.get("default", [])
```

### Benefits

1. **Improved API Usability**: Users can work with human-readable enum names instead of magic numbers
2. **Consistency**: Provides the same enum support across all library interfaces
3. **Maintainability**: Single implementation point for enum parameter conversion logic
4. **Extendability**: Decorator can be applied to other methods that need similar functionality
5. **Minimal Changes**: Existing code remains largely untouched

### Required Changes

1. Add the `with_enum_param` decorator to `m8/core/enums.py`
2. Add the `get_fx_keys_enum_paths` function to `m8/config.py`
3. Update `format_config.yaml` to include FX enum mappings if not already present
4. Add decorators to relevant methods in `M8PhraseStep` and potentially other classes
5. Update tests to verify both numeric and string enum values work correctly

### Potential Extensions

This pattern could be extended to other parts of the API that might benefit from enum string support:

- Other parameter types in instrument classes
- Chain and phrase management functions
- Any method where users currently need to work with numeric IDs

### Implementation Priority

This enhancement should be considered medium priority:
- It improves API usability significantly
- It's consistent with the library's goal of providing intuitive interfaces
- It doesn't require extensive changes to the codebase