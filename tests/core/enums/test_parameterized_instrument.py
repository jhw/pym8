import unittest
from m8.api.instruments import M8Instrument
from m8.enums.wavsynth import M8WavSynthShapes
from m8.enums.macrosynth import M8MacroSynthShapes
from m8.enums.sampler import M8SamplerPlayMode
from m8.enums import M8FilterTypes, M8LimitTypes, M8InstrumentType

class TestParameterizedInstruments(unittest.TestCase):
    """Parameterized tests for instrument functionality that can be applied to all types."""
    
    def setUp(self):
        # Define test data for all instrument types with their specific parameters
        self.test_data = [
            {
                "name": "WavSynth",
                "instrument_type": "WAVSYNTH",
                "type_id": 0x00,
                "type_enum": M8InstrumentType.WAVSYNTH,
                "params": {
                    "shape": {
                        "param_name": "shape",
                        "string_value": "PULSE25",
                        "numeric_value": M8WavSynthShapes.PULSE25.value,
                        "offset": 18
                    },
                    "filter": {
                        "param_name": "filter",
                        "string_value": "HIGHPASS",
                        "numeric_value": M8FilterTypes.HIGHPASS.value,
                        "offset": 23
                    },
                    "limit": {
                        "param_name": "limit",
                        "string_value": "FOLD",
                        "numeric_value": M8LimitTypes.FOLD.value,
                        "offset": 27
                    }
                }
            },
            {
                "name": "MacroSynth",
                "instrument_type": "MACROSYNTH",
                "type_id": 0x01,
                "type_enum": M8InstrumentType.MACROSYNTH,
                "params": {
                    "shape": {
                        "param_name": "shape",
                        "string_value": "MORPH",
                        "numeric_value": M8MacroSynthShapes.MORPH.value,
                        "offset": 18
                    },
                    "filter": {
                        "param_name": "filter",
                        "string_value": "HIGHPASS",
                        "numeric_value": M8FilterTypes.HIGHPASS.value,
                        "offset": 23
                    },
                    "limit": {
                        "param_name": "limit",
                        "string_value": "FOLD",
                        "numeric_value": M8LimitTypes.FOLD.value,
                        "offset": 27
                    }
                }
            },
            {
                "name": "Sampler",
                "instrument_type": "SAMPLER",
                "type_id": 0x02,
                "type_enum": M8InstrumentType.SAMPLER,
                "params": {
                    "play_mode": {
                        "param_name": "play_mode",
                        "string_value": "REV",
                        "numeric_value": M8SamplerPlayMode.REV.value,
                        "offset": 18
                    },
                    "filter": {
                        "param_name": "filter",
                        "string_value": "HIGHPASS",
                        "numeric_value": M8FilterTypes.HIGHPASS.value,
                        "offset": 24
                    },
                    "limit": {
                        "param_name": "limit",
                        "string_value": "FOLD",
                        "numeric_value": M8LimitTypes.FOLD.value,
                        "offset": 28
                    }
                }
            }
        ]
    
    def test_constructor_with_string_enums(self):
        """Test using string enum values in instrument constructors."""
        for instrument_data in self.test_data:
            # Build constructor kwargs with string enum values
            kwargs = {
                "instrument_type": instrument_data["instrument_type"],
                "name": f"Test{instrument_data['name']}"
            }
            
            # Add all parameter values
            for param_name, param_data in instrument_data["params"].items():
                kwargs[param_name] = param_data["string_value"]
            
            # Create instrument with string enum values
            instrument = M8Instrument(**kwargs)
            
            # Verify type ID
            self.assertEqual(instrument.type, instrument_data["type_id"])
            
            # Verify string enums are preserved in object properties
            for param_name, param_data in instrument_data["params"].items():
                self.assertEqual(
                    getattr(instrument.params, param_name),
                    param_data["string_value"],
                    f"String enum value not preserved for {param_name} in {instrument_data['name']}"
                )
            
            # Write to binary and check numeric values
            binary = instrument.write()
            
            # Check all parameters' binary representation
            for param_name, param_data in instrument_data["params"].items():
                offset = param_data["offset"]
                self.assertEqual(
                    binary[offset],
                    param_data["numeric_value"],
                    f"Binary value incorrect for {param_name} in {instrument_data['name']}"
                )
    
    def test_from_dict_with_string_enums(self):
        """Test creating instruments from dictionary with string enum values."""
        for instrument_data in self.test_data:
            # Prepare dictionary with string enum values
            dict_data = {
                "type": instrument_data["type_enum"].name,
                "name": f"Test{instrument_data['name']}"
            }
            
            # Add all parameter values
            for param_name, param_data in instrument_data["params"].items():
                dict_data[param_name] = param_data["string_value"]
            
            # Create instrument from dictionary
            instrument = M8Instrument.from_dict(dict_data)
            
            # Verify type ID
            self.assertEqual(instrument.type, instrument_data["type_id"])
            
            # Verify string enums are preserved in object properties
            for param_name, param_data in instrument_data["params"].items():
                self.assertEqual(
                    getattr(instrument.params, param_name),
                    param_data["string_value"],
                    f"String enum not preserved from dict for {param_name} in {instrument_data['name']}"
                )
            
            # Write to binary and check numeric values
            binary = instrument.write()
            
            # Check all parameters' binary representation
            for param_name, param_data in instrument_data["params"].items():
                offset = param_data["offset"]
                self.assertEqual(
                    binary[offset],
                    param_data["numeric_value"],
                    f"Binary value incorrect after from_dict for {param_name} in {instrument_data['name']}"
                )
    
    def test_as_dict_with_enum_serialization(self):
        """Test serialization of instrument parameters with enum values."""
        for instrument_data in self.test_data:
            # Build constructor kwargs with numeric enum values
            kwargs = {
                "instrument_type": instrument_data["instrument_type"],
                "name": f"Test{instrument_data['name']}"
            }
            
            # Add all parameter values as numeric
            for param_name, param_data in instrument_data["params"].items():
                kwargs[param_name] = param_data["numeric_value"]
            
            # Create instrument with numeric enum values
            instrument = M8Instrument(**kwargs)
            
            # Convert to dict
            result = instrument.as_dict()
            
            # Verify type string
            self.assertEqual(result["type"], instrument_data["type_enum"].name)
            
            # Verify numeric values converted to strings in dictionary
            for param_name, param_data in instrument_data["params"].items():
                self.assertEqual(
                    result[param_name],
                    param_data["string_value"],
                    f"Enum not properly serialized for {param_name} in {instrument_data['name']}"
                )

if __name__ == '__main__':
    unittest.main()