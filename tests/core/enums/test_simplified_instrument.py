import unittest
from m8.api.instruments import M8Instrument
from m8.enums.wavsynth import M8WavSynthShapes
from m8.enums.macrosynth import M8MacroSynthShapes
from m8.enums import M8FilterTypes, M8LimitTypes, M8InstrumentType

class TestInstrumentEnumSupport(unittest.TestCase):
    """Simplified tests for instrument enum support using the enums utility module."""
    
    def setUp(self):
        # Test data for wavsynth and macrosynth
        self.test_data = [
            {
                "instrument_type": "WAVSYNTH",
                "type_id": 0x00,
                "type_string": "WAVSYNTH",
                "shape_enum": M8WavSynthShapes,
                "shape_string": "PULSE25",
                "shape_numeric": M8WavSynthShapes.PULSE25.value
            },
            {
                "instrument_type": "MACROSYNTH",
                "type_id": 0x01,
                "type_string": "MACROSYNTH",
                "shape_enum": M8MacroSynthShapes,
                "shape_string": "MORPH",
                "shape_numeric": M8MacroSynthShapes.MORPH.value
            }
        ]
    
    def test_constructor_with_string_enums(self):
        """Test using string enum values with instrument constructor."""
        for data in self.test_data:
            # Create instrument with string enum values
            instrument = M8Instrument(
                instrument_type=data["instrument_type"],
                shape=data["shape_string"],
                filter="HIGHPASS",
                limit="FOLD"
            )
            
            # Check type ID was set correctly
            self.assertEqual(instrument.type, data["type_id"])
            
            # Check shape parameter preserves string
            self.assertEqual(instrument.params.shape, data["shape_string"])
            
            # Check filter parameter
            self.assertEqual(instrument.params.filter, "HIGHPASS")
            
            # Check limit parameter
            self.assertEqual(instrument.params.limit, "FOLD")
            
            # Write to binary and check numeric values in output
            binary = instrument.write()
            
            # Check shape value in binary
            self.assertEqual(binary[18], data["shape_numeric"])
            
            # Check filter value in binary (HIGHPASS = 2)
            self.assertEqual(binary[23], M8FilterTypes.HIGHPASS.value)
            
            # Check limit value in binary (FOLD = 2)
            self.assertEqual(binary[27], M8LimitTypes.FOLD.value)
    
    def test_as_dict_with_enum_serialization(self):
        """Test serialization of instrument parameters with enum values."""
        for data in self.test_data:
            # Create instrument with numeric enum values
            instrument = M8Instrument(
                instrument_type=data["instrument_type"],
                shape=data["shape_numeric"],
                filter=M8FilterTypes.HIGHPASS.value,
                limit=M8LimitTypes.FOLD.value
            )
            
            # Convert to dict
            result = instrument.as_dict()
            
            # Type should be serialized to enum string
            self.assertEqual(result["type"], data["type_string"])
            
            # Shape should be serialized to enum string
            self.assertEqual(result["shape"], data["shape_string"])
            
            # Filter should be serialized to enum string
            self.assertEqual(result["filter"], "HIGHPASS")
            
            # Limit should be serialized to enum string
            self.assertEqual(result["limit"], "FOLD")
    
    def test_from_dict_with_string_enums(self):
        """Test deserialization of dictionary with string enum values."""
        for data in self.test_data:
            # Create a dictionary with string enum values
            dict_data = {
                "type": data["type_string"],
                "shape": data["shape_string"],
                "filter": "HIGHPASS",
                "limit": "FOLD"
            }
            
            # Create instrument from dictionary
            instrument = M8Instrument.from_dict(dict_data)
            
            # Check type was set correctly
            self.assertEqual(instrument.type, data["type_id"])
            
            # Check shape parameter preserves string
            self.assertEqual(instrument.params.shape, data["shape_string"])
            
            # Check filter parameter
            self.assertEqual(instrument.params.filter, "HIGHPASS")
            
            # Check limit parameter
            self.assertEqual(instrument.params.limit, "FOLD")
            
            # Write to binary and check numeric values
            binary = instrument.write()
            
            # Check shape value in binary
            self.assertEqual(binary[18], data["shape_numeric"])
            
            # Check filter value in binary (HIGHPASS = 2)
            self.assertEqual(binary[23], M8FilterTypes.HIGHPASS.value)
            
            # Check limit value in binary (FOLD = 2)
            self.assertEqual(binary[27], M8LimitTypes.FOLD.value)

if __name__ == '__main__':
    unittest.main()