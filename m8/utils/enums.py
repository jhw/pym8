from enum import IntEnum

def concat_enums(*enum_classes, name="ConcatenatedEnum"):
    if len(enum_classes) < 2:
        raise ValueError("At least two Enum classes must be provided")
    
    # Collect all members
    all_items = {}
    all_values = set()
    
    for enum_class in enum_classes:
        for key, member in enum_class.__members__.items():
            # Check for duplicate keys
            if key in all_items:
                raise ValueError(f"Duplicate key '{key}' found across Enum classes")
            
            # Check for duplicate values
            if member.value in all_values:
                raise ValueError(f"Duplicate value {member.value} found across Enum classes")
            
            all_items[key] = member.value
            all_values.add(member.value)
    
    # Create and return the new IntEnum class
    return IntEnum(name, all_items)
