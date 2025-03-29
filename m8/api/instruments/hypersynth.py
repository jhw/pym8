# m8/api/instruments/hypersynth.py
from m8.api.instruments import M8Instrument

class M8HyperSynth(M8Instrument):
    """M8 Hyper Synthesizer instrument type.
    
    This is a skeleton implementation for a hypothetical HyperSynth instrument type.
    """
    
    def __init__(self, **kwargs):
        """Initialize a new HyperSynth instrument."""
        # Call parent constructor with HYPERSYNTH type
        super().__init__(instrument_type="HYPERSYNTH", **kwargs)
    
    @classmethod
    def from_dict(cls, data):
        """Create a HyperSynth instrument from dictionary data."""
        # Create a copy of the data without modifying the original
        data_copy = data.copy()
        
        # Ensure type is set correctly
        data_copy["type"] = "HYPERSYNTH"
        
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