import inspect
import functools

def auto_name_decorator(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # Only try to get the name if not explicitly provided
        if 'name' not in kwargs or kwargs['name'] is None:
            frame = inspect.currentframe().f_back
            call_line = inspect.getframeinfo(frame).code_context[0].strip()
            
            # Extract the variable name from an assignment
            if "=" in call_line:
                var_name = call_line.split("=")[0].strip()
                kwargs['name'] = var_name
        
        # If we still don't have a name, use a default
        if 'name' not in kwargs or kwargs['name'] is None:
            kwargs['name'] = f"M8{func.__name__.replace('m8_', '').replace('_class', '').capitalize()}"
            
        return func(*args, **kwargs)
    
    return wrapper


