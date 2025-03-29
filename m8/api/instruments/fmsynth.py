# m8/api/instruments/fmsynth.py
from m8.api.instruments import M8Instrument
from m8.core.enums import EnumPropertyMixin
from m8.api import ensure_enum_int_value, serialize_param_enum_value
from m8.config import load_format_config
import importlib

class FMOperator:
    """A single FM operator group with its parameters."""
    
    def __init__(self, shape=0, ratio=0, level=0, feedback=0, mod_a=0, mod_b=0):
        """Initialize a new FM operator with the given parameters."""
        self.shape = shape
        self.ratio = ratio
        self.level = level
        self.feedback = feedback
        self.mod_a = mod_a
        self.mod_b = mod_b
    
    def as_dict(self):
        """Convert operator to dictionary for serialization."""
        return {
            "shape": self.shape,
            "ratio": self.ratio,
            "level": self.level,
            "feedback": self.feedback,
            "mod_a": self.mod_a,
            "mod_b": self.mod_b
        }
    
    @classmethod
    def from_dict(cls, data):
        """Create an operator from a dictionary."""
        return cls(
            shape=data.get("shape", 0),
            ratio=data.get("ratio", 0),
            level=data.get("level", 0),
            feedback=data.get("feedback", 0),
            mod_a=data.get("mod_a", 0),
            mod_b=data.get("mod_b", 0)
        )


class M8FMSynth(M8Instrument):
    """M8 FM Synthesizer instrument type with operator groups."""
    
    def __init__(self, operators=None, algo=0, **kwargs):
        """Initialize a new FMSynth instrument with operators."""
        # Call parent constructor with FMSYNTH type first
        # This will create the params object with default parameters
        super().__init__(instrument_type="FMSYNTH", algo=algo, **kwargs)
        
        # Set up operators if provided, otherwise create default operators
        self._operators = operators or [FMOperator() for _ in range(4)]
        
        # Ensure we have exactly 4 operators
        if len(self._operators) != 4:
            raise ValueError("FMSynth must have exactly 4 operators")
            
        # Map operator parameters to underlying params if operators were provided
        if operators:
            self._map_operators_to_params()
    
    def _map_operators_to_params(self):
        """Map operator parameters to underlying instrument parameters."""
        # Set parameters for each operator
        for i, op in enumerate(self._operators):
            idx = i + 1  # Parameters are 1-indexed
            
            # Map operator parameters to underlying params
            setattr(self.params, f"shape{idx}", op.shape)
            setattr(self.params, f"ratio{idx}", op.ratio)
            setattr(self.params, f"level{idx}", op.level)
            setattr(self.params, f"feedback{idx}", op.feedback)
            setattr(self.params, f"mod_a{idx}", op.mod_a)
            setattr(self.params, f"mod_b{idx}", op.mod_b)
    
    def _map_params_to_operators(self):
        """Map underlying instrument parameters to operators."""
        # Update operators from parameters
        for i in range(4):
            idx = i + 1  # Parameters are 1-indexed
            
            # Get values from params
            shape = getattr(self.params, f"shape{idx}", 0)
            ratio = getattr(self.params, f"ratio{idx}", 0)
            level = getattr(self.params, f"level{idx}", 0)
            feedback = getattr(self.params, f"feedback{idx}", 0)
            mod_a = getattr(self.params, f"mod_a{idx}", 0)
            mod_b = getattr(self.params, f"mod_b{idx}", 0)
            
            # Update operator
            self._operators[i] = FMOperator(
                shape=shape,
                ratio=ratio,
                level=level,
                feedback=feedback,
                mod_a=mod_a,
                mod_b=mod_b
            )
    
    @property
    def operators(self):
        """Get the FM operators."""
        # Ensure operators are synced with parameters
        self._map_params_to_operators()
        return self._operators
    
    @operators.setter
    def operators(self, operators):
        """Set the FM operators."""
        if len(operators) != 4:
            raise ValueError("FMSynth must have exactly 4 operators")
        
        self._operators = operators
        self._map_operators_to_params()
    
    def _read_parameters(self, data):
        """Read parameters from binary data and update operators."""
        # Read all parameters using parent method
        super()._read_parameters(data)
        
        # Update operators from parameters
        self._map_params_to_operators()
    
    def as_dict(self):
        """Convert instrument to dictionary for serialization."""
        # Get base dictionary from parent which already has all param conversions
        result = super().as_dict()
        
        # Create operators array with values from parameters
        operators = []
        for i in range(4):
            idx = i + 1  # 1-indexed
            
            # Create operator dict directly from the corresponding parameters
            # This avoids duplicating enum conversion logic
            op_dict = {
                "shape": result.get(f"shape{idx}"),
                "ratio": result.get(f"ratio{idx}"),
                "level": result.get(f"level{idx}"),
                "feedback": result.get(f"feedback{idx}"),
                "mod_a": result.get(f"mod_a{idx}"),
                "mod_b": result.get(f"mod_b{idx}")
            }
            
            operators.append(op_dict)
        
        # Add operators to result
        result["operators"] = operators
        
        return result
    
    @classmethod
    def from_dict(cls, data):
        """Create an FMSynth instrument from dictionary data."""
        # Create a copy of the data without modifying the original
        data_copy = data.copy()
        
        # Ensure type is set correctly
        data_copy["type"] = "FMSYNTH"
        
        # Extract operators if present
        operators = None
        if "operators" in data_copy:
            operators_data = data_copy.pop("operators")
            
            # Map operator values to actual parameters
            for i, op_data in enumerate(operators_data):
                if i >= 4:  # Only process 4 operators
                    break
                    
                idx = i + 1  # 1-indexed parameter names
                
                # Copy operator values to corresponding parameter fields
                if "shape" in op_data:
                    data_copy[f"shape{idx}"] = op_data["shape"]
                if "ratio" in op_data:
                    data_copy[f"ratio{idx}"] = op_data["ratio"]
                if "level" in op_data:
                    data_copy[f"level{idx}"] = op_data["level"]
                if "feedback" in op_data:
                    data_copy[f"feedback{idx}"] = op_data["feedback"]
                if "mod_a" in op_data:
                    data_copy[f"mod_a{idx}"] = op_data["mod_a"]
                if "mod_b" in op_data:
                    data_copy[f"mod_b{idx}"] = op_data["mod_b"]
        
        # Let the parent handle all parameter conversion including enums
        instance = super().from_dict(data_copy)
        
        # Map parameters to operators
        instance._map_params_to_operators()
        
        return instance