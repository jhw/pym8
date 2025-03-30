# m8/api/instruments/hypersynth.py
from m8.api.instruments import M8Instrument

class M8HyperSynth(M8Instrument):
    """M8 Hyper Synthesizer instrument type.
    
    The HyperSynth has a 6-note scale/chord implementation that is exposed as
    individual parameters (note1-6) in the binary format, but as a consolidated
    "notes" list in the JSON serialization for easier manipulation.
    """
    
    def __init__(self, notes=None, **kwargs):
        """Initialize a new HyperSynth instrument.
        
        Args:
            notes: Optional list of 6 note values, which will be set as note1-6
            **kwargs: Other instrument parameters
        """
        # Handle notes specially if provided
        if notes is not None:
            if len(notes) != 6:
                raise ValueError("HyperSynth notes must be a list of exactly 6 values")
            
            # Extract notes into individual parameters
            for i, note in enumerate(notes):
                kwargs[f"note{i+1}"] = note
        
        # Call parent constructor with HYPERSYNTH type
        super().__init__(instrument_type="HYPERSYNTH", **kwargs)
    
    @property
    def notes(self):
        """Get the notes as a list of 6 values."""
        return [
            getattr(self.params, f"note{i+1}", 0)
            for i in range(6)
        ]
    
    @notes.setter
    def notes(self, value):
        """Set the notes from a list of 6 values."""
        if len(value) != 6:
            raise ValueError("HyperSynth notes must be a list of exactly 6 values")
        
        for i, note in enumerate(value):
            setattr(self.params, f"note{i+1}", note)
    
    def as_dict(self):
        """Convert instrument to dictionary for serialization.
        
        The individual note1-6 parameters are combined into a single 'notes' list
        for a more structured representation.
        """
        # Get base dictionary from parent
        result = super().as_dict()
        
        # Extract individual note parameters into a notes list
        notes = []
        for i in range(1, 7):
            note_key = f"note{i}"
            if note_key in result:
                notes.append(result[note_key])
                # Remove the individual note key
                del result[note_key]
        
        # Add the notes list to the result
        result["notes"] = notes
        
        return result
    
    @classmethod
    def from_dict(cls, data):
        """Create a HyperSynth instrument from dictionary data.
        
        Handles the 'notes' list by expanding it to individual note1-6 parameters.
        """
        # Create a copy of the data without modifying the original
        data_copy = data.copy()
        
        # Ensure type is set correctly
        data_copy["type"] = "HYPERSYNTH"
        
        # Extract notes if present and expand to individual parameters
        if "notes" in data_copy:
            notes = data_copy.pop("notes")
            if len(notes) != 6:
                raise ValueError("HyperSynth notes must be a list of exactly 6 values")
            
            for i, note in enumerate(notes):
                data_copy[f"note{i+1}"] = note
        
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