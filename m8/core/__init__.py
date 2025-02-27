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

def set_caller_module_decorator(factory_func):
    """
    Decorator that sets the __module__ attribute of classes created by factory functions
    to the module where they are being assigned, not where the factory is defined.
    """
    @functools.wraps(factory_func)
    def wrapper(*args, **kwargs):
        # Call the original factory function to create the class
        cls = factory_func(*args, **kwargs)
        
        # Get caller's frame to determine where this class is being assigned
        caller_frame = inspect.currentframe().f_back
        caller_module = inspect.getmodule(caller_frame)
        caller_module_name = caller_module.__name__
        
        # Override __module__ to reflect where the class is being assigned
        cls.__module__ = caller_module_name
        
        # Make sure the class name is preserved from the name parameter
        if 'name' in kwargs and kwargs['name'] is not None:
            cls.__name__ = kwargs['name']
        
        return cls
    
    return wrapper
