import unittest
from enum import Enum, IntEnum, auto

# Import the function to test (assuming it's in a module called 'enum_utils')
from m8.utils.enums import concat_enums

class TestEnums(unittest.TestCase):
    
    def setUp(self):
        # Define some test enums
        class ColorEnum(IntEnum):
            RED = 1
            GREEN = 2
            BLUE = 3
        
        class ShapeEnum(IntEnum):
            CIRCLE = 4
            SQUARE = 5
            TRIANGLE = 6
        
        class StatusEnum(IntEnum):
            ACTIVE = 100
            INACTIVE = 200
            PENDING = 300
        
        self.ColorEnum = ColorEnum
        self.ShapeEnum = ShapeEnum
        self.StatusEnum = StatusEnum
    
    def test_basic_concatenation(self):
        # Test basic concatenation of two enums
        CombinedEnum = concat_enums(self.ColorEnum, self.ShapeEnum)
        
        # Check that the result is an IntEnum class
        self.assertTrue(issubclass(CombinedEnum, IntEnum))
        
        # Check that all members from both source enums are present
        self.assertEqual(CombinedEnum.RED.value, 1)
        self.assertEqual(CombinedEnum.GREEN.value, 2)
        self.assertEqual(CombinedEnum.BLUE.value, 3)
        self.assertEqual(CombinedEnum.CIRCLE.value, 4)
        self.assertEqual(CombinedEnum.SQUARE.value, 5)
        self.assertEqual(CombinedEnum.TRIANGLE.value, 6)
        
        # Check member count
        self.assertEqual(len(CombinedEnum.__members__), 6)
        
        # Verify IntEnum behavior - members can be used in calculations
        self.assertEqual(CombinedEnum.RED + 10, 11)
    
    def test_custom_name(self):
        # Test with custom name
        CustomNameEnum = concat_enums(self.ColorEnum, self.ShapeEnum, name="CustomNameEnum")
        self.assertEqual(CustomNameEnum.__name__, "CustomNameEnum")
    
    def test_multiple_enums(self):
        # Test concatenation of three enums
        TripleEnum = concat_enums(self.ColorEnum, self.ShapeEnum, self.StatusEnum)
        
        # Check member count and some values
        self.assertEqual(len(TripleEnum.__members__), 9)
        self.assertEqual(TripleEnum.RED.value, 1)
        self.assertEqual(TripleEnum.SQUARE.value, 5)
        self.assertEqual(TripleEnum.PENDING.value, 300)
    
    def test_error_on_key_collision(self):
        # Create an enum with duplicate key
        class AnotherEnum(IntEnum):
            RED = 10  # Same key as ColorEnum.RED but different value
            OVAL = 11
        
        # Should raise ValueError due to key collision
        with self.assertRaises(ValueError) as context:
            concat_enums(self.ColorEnum, AnotherEnum)
        
        self.assertIn("Duplicate key", str(context.exception))
    
    def test_error_on_value_collision(self):
        # Create an enum with duplicate value
        class AnotherEnum(IntEnum):
            CRIMSON = 1  # Different key but same value as ColorEnum.RED
            OVAL = 11
        
        # Should raise ValueError due to value collision
        with self.assertRaises(ValueError) as context:
            concat_enums(self.ColorEnum, AnotherEnum)
        
        self.assertIn("Duplicate value", str(context.exception))
    
    def test_error_on_single_enum(self):
        # Should raise ValueError when only one enum is provided
        with self.assertRaises(ValueError) as context:
            concat_enums(self.ColorEnum)
        
        self.assertIn("At least two Enum classes", str(context.exception))
    
    def test_mixed_enum_types(self):
        # Regular Enum with int values should work with IntEnum
        class RegularEnum(Enum):
            A = 7
            B = 8
        
        MixedEnum = concat_enums(self.ColorEnum, RegularEnum)
        
        # Result should be IntEnum
        self.assertTrue(issubclass(MixedEnum, IntEnum))
        self.assertEqual(MixedEnum.A.value, 7)
        self.assertEqual(MixedEnum.RED.value, 1)
        
        # Should support integer operations
        self.assertEqual(MixedEnum.A + 3, 10)
    
    def test_auto_enums(self):
        # Test with auto-generated enum values
        class FirstEnum(IntEnum):
            A = auto()
            B = auto()
        
        class SecondEnum(IntEnum):
            C = auto()
            D = auto()
        
        # Auto values should start from 1 in each enum
        # So we'd expect A=1, B=2, C=1, D=2, which would cause value collision
        with self.assertRaises(ValueError) as context:
            concat_enums(FirstEnum, SecondEnum)
        
        self.assertIn("Duplicate value", str(context.exception))

if __name__ == '__main__':
    unittest.main()
