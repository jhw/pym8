import unittest
from tests.core.enums.test_logging_config import *  # Import to suppress context warnings
from m8.api.modulators import M8Modulator
from m8.core.enums import serialize_enum, deserialize_enum
from m8.enums.wavsynth import M8WavSynthModDestinations
from m8.enums.macrosynth import M8MacroSynthModDestinations
from m8.enums.sampler import M8SamplerModDestinations

class TestModulatorEnumSupport(unittest.TestCase):
    """Simplified tests for modulator enum support using the enums utility module."""
    
    def test_constructor_with_string_enums(self):
        """Test using string enum values with modulator constructor."""
        # WavSynth destination
        mod_wavsynth = M8Modulator(
            modulator_type="LFO",
            instrument_type=0x00,  # WavSynth
            destination="CUTOFF",  # String enum value
            amount=0x80
        )
        
        # MacroSynth destination
        mod_macrosynth = M8Modulator(
            modulator_type="LFO",
            instrument_type=0x01,  # MacroSynth
            destination="TIMBRE",  # String enum value
            amount=0x80
        )
        
        # Sampler destination
        mod_sampler = M8Modulator(
            modulator_type="LFO",
            instrument_type=0x02,  # Sampler
            destination="CUTOFF",  # String enum value
            amount=0x80
        )
        
        # String values should be preserved in object properties
        self.assertEqual(mod_wavsynth.destination, "CUTOFF")
        self.assertEqual(mod_macrosynth.destination, "TIMBRE")
        self.assertEqual(mod_sampler.destination, "CUTOFF")
        
        # When writing to binary, the correct numeric values should be used
        wavsynth_binary = mod_wavsynth.write()
        macrosynth_binary = mod_macrosynth.write()
        sampler_binary = mod_sampler.write()
        
        # Verify correct numeric values in binary output
        self.assertEqual(wavsynth_binary[0] & 0x0F, M8WavSynthModDestinations.CUTOFF.value)
        self.assertEqual(macrosynth_binary[0] & 0x0F, M8MacroSynthModDestinations.TIMBRE.value)
        self.assertEqual(sampler_binary[0] & 0x0F, M8SamplerModDestinations.CUTOFF.value)
    
    def test_as_dict_with_enum_serialization(self):
        """Test serialization of modulator parameters with enum values."""
        # Using numeric values for creation
        mod_wavsynth = M8Modulator(
            modulator_type="LFO",
            instrument_type=0x00,  # WavSynth
            destination=M8WavSynthModDestinations.CUTOFF.value,
            amount=0x80
        )
        
        mod_macrosynth = M8Modulator(
            modulator_type="LFO",
            instrument_type=0x01,  # MacroSynth
            destination=M8MacroSynthModDestinations.TIMBRE.value,
            amount=0x80
        )
        
        # Convert to dict - should have string enum values
        result_wavsynth = mod_wavsynth.as_dict()
        result_macrosynth = mod_macrosynth.as_dict()
        
        # Enum values should be serialized to strings
        self.assertEqual(result_wavsynth["destination"], "CUTOFF")
        self.assertEqual(result_macrosynth["destination"], "TIMBRE")
    
    def test_from_dict_with_string_enums(self):
        """Test deserialization of dictionary with string enum values."""
        # Dictionaries with string enum values
        wavsynth_data = {
            "type": "LFO",
            "destination": "CUTOFF",  # String enum value
            "amount": 0x80,
            "oscillator": 0x1
        }
        
        macrosynth_data = {
            "type": "LFO", 
            "destination": "TIMBRE",  # String enum value
            "amount": 0x80,
            "oscillator": 0x1
        }
        
        # Create modulators from dictionaries with instrument_type context
        mod_wavsynth = M8Modulator.from_dict(wavsynth_data, instrument_type=0x00)
        mod_macrosynth = M8Modulator.from_dict(macrosynth_data, instrument_type=0x01)
        
        # String values should be preserved in the objects
        self.assertEqual(mod_wavsynth.destination, "CUTOFF")
        self.assertEqual(mod_macrosynth.destination, "TIMBRE")
        
        # When writing to binary, the correct numeric values should be used
        wavsynth_binary = mod_wavsynth.write()
        macrosynth_binary = mod_macrosynth.write()
        
        # The destination is in the lower nibble of the first byte
        self.assertEqual(wavsynth_binary[0] & 0x0F, M8WavSynthModDestinations.CUTOFF.value)
        self.assertEqual(macrosynth_binary[0] & 0x0F, M8MacroSynthModDestinations.TIMBRE.value)
    
    def test_parameterized_instrument_types(self):
        """Demonstrate parameterized testing approach for instrument types."""
        # Test data for multiple instrument types
        test_data = [
            {
                "instrument_type": 0x00,  # WavSynth
                "enum_class": M8WavSynthModDestinations,
                "string_value": "CUTOFF",
                "numeric_value": M8WavSynthModDestinations.CUTOFF.value
            },
            {
                "instrument_type": 0x01,  # MacroSynth
                "enum_class": M8MacroSynthModDestinations,
                "string_value": "TIMBRE",
                "numeric_value": M8MacroSynthModDestinations.TIMBRE.value
            },
            {
                "instrument_type": 0x02,  # Sampler
                "enum_class": M8SamplerModDestinations,
                "string_value": "CUTOFF",
                "numeric_value": M8SamplerModDestinations.CUTOFF.value
            }
        ]
        
        # Run tests for each instrument type
        for data in test_data:
            # Create modulator with string enum
            mod = M8Modulator(
                modulator_type="LFO",
                instrument_type=data["instrument_type"],
                destination=data["string_value"],
                amount=0x80
            )
            
            # Check string value preserved
            self.assertEqual(mod.destination, data["string_value"])
            
            # Check correct binary representation
            binary = mod.write()
            self.assertEqual(binary[0] & 0x0F, data["numeric_value"])

if __name__ == '__main__':
    unittest.main()