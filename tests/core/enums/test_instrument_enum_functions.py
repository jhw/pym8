import unittest
from m8.core.enums import (
    get_enum_paths_for_instrument,
    load_enum_classes
)

class TestInstrumentEnumFunctions(unittest.TestCase):
    def test_get_enum_paths_for_instrument(self):
        # Setup test enum paths
        enum_paths = {
            "0x00": ["m8.enums.wavsynth.TestWavSynthEnum"],
            "0x01": ["m8.enums.macrosynth.TestMacroSynthEnum"],
            "0x02": ["m8.enums.sampler.TestSamplerEnum"]
        }
        
        # Test with different instrument types
        self.assertEqual(
            get_enum_paths_for_instrument(enum_paths, 0x00),
            ["m8.enums.wavsynth.TestWavSynthEnum"]
        )
        
        self.assertEqual(
            get_enum_paths_for_instrument(enum_paths, "0x01"),
            ["m8.enums.macrosynth.TestMacroSynthEnum"]
        )
        
        # Test with string numeric value
        self.assertEqual(
            get_enum_paths_for_instrument(enum_paths, "0"),
            ["m8.enums.wavsynth.TestWavSynthEnum"]
        )
        
        # Test with non-dict
        non_dict_paths = ["some.enum.path"]
        self.assertEqual(
            get_enum_paths_for_instrument(non_dict_paths, 0x00),
            non_dict_paths
        )
        
        # Test with None instrument type
        self.assertEqual(
            get_enum_paths_for_instrument(enum_paths, None),
            enum_paths
        )
        
        # Test with missing instrument type
        self.assertIsNone(
            get_enum_paths_for_instrument(enum_paths, 0x03)
        )
    
    def test_load_enum_classes(self):
        # This test uses real enums from the codebase
        enum_paths = ["m8.enums.M8FilterTypes", "m8.enums.M8LimitTypes"]
        
        # Load enum classes
        enum_classes = load_enum_classes(enum_paths)
        
        # Verify correct enum classes were loaded
        self.assertEqual(len(enum_classes), 2)
        self.assertEqual(enum_classes[0].__name__, "M8FilterTypes")
        self.assertEqual(enum_classes[1].__name__, "M8LimitTypes")
        
        # Test with single string path
        single_enum_class = load_enum_classes("m8.enums.M8FilterTypes")
        self.assertEqual(len(single_enum_class), 1)
        self.assertEqual(single_enum_class[0].__name__, "M8FilterTypes")
        
        # Test with empty path
        self.assertEqual(load_enum_classes(None), [])
        self.assertEqual(load_enum_classes([]), [])
        
        # Test with invalid path
        self.assertEqual(load_enum_classes(["invalid.module.path"]), [])


if __name__ == '__main__':
    unittest.main()