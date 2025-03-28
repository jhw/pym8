# m8/api/instruments/sampler.py
from m8.api.instruments import M8Instrument

class M8Sampler(M8Instrument):
    """M8 Sampler instrument type."""
    
    def __init__(self, **kwargs):
        """Initialize a new Sampler instrument."""
        # Call parent constructor with SAMPLER type
        super().__init__(instrument_type="SAMPLER", **kwargs)
    
    @classmethod
    def from_dict(cls, data):
        """Create a Sampler instrument from dictionary data."""
        # Create a copy of the data without modifying the original
        data_copy = data.copy()
        
        # Ensure type is set correctly
        data_copy["type"] = "SAMPLER"
        
        # Create instance using parent class method
        instance = super().from_dict(data_copy)
        
        # Return the instance if it's already our class, otherwise create a new one
        if isinstance(instance, cls):
            return instance
        
        # If the factory didn't create our class, create a new one with the params from instance
        result = cls()
        for key, value in vars(instance).items():
            setattr(result, key, value)
        
        return result