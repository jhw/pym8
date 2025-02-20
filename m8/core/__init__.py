_m8_class_counter = 0

def m8_class_name(prefix="M8"):
    global _m8_class_counter
    _m8_class_counter += 1
    return f"{prefix}_{_m8_class_counter}"
    
