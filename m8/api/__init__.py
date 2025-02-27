class M8ValidationError(Exception):
    pass

class M8IndexError(IndexError):
    pass

def load_class(class_path):
    module_name, class_name = class_path.rsplit('.', 1)
    module = __import__(module_name, fromlist=[class_name])
    return getattr(module, class_name)
