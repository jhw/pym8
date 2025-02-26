from m8.core.fields import M8Field, M8FieldMap

import struct
import unittest

class TestM8Field(unittest.TestCase):
    def test_field_initialization(self):
        """Test basic field initialization"""
        # Test regular field
        field = M8Field("single_byte", 0x42, 0, 1, "UINT8")
        self.assertEqual(field.name, "single_byte")
        self.assertEqual(field.default, 0x42)
        self.assertEqual(field.start, 0)
        self.assertEqual(field.end, 1)
        self.assertEqual(field.format, "UINT8")
        self.assertFalse(field.is_composite)
        
        # Test composite field
        field = M8Field("upper|lower", 0x12, 1, 2, "UINT4_2")
        self.assertEqual(field.name, "upper|lower")
        self.assertEqual(field.default, 0x12)
        self.assertTrue(field.is_composite)
        self.assertEqual(field.parts, ["upper", "lower"])
        
        # Test string field
        field = M8Field("text", "TEST", 6, 10, "STRING")
        self.assertEqual(field.name, "text")
        self.assertEqual(field.default, "TEST")
        self.assertEqual(field.format, "STRING")
        
        # Test float field
        field = M8Field("floating", 1.5, 2, 6, "FLOAT32")
        self.assertEqual(field.name, "floating")
        self.assertAlmostEqual(field.default, 1.5)
        self.assertEqual(field.format, "FLOAT32")
        
        # Test invalid format
        with self.assertRaises(ValueError):
            M8Field("invalid", 0, 0, 1, "INVALID_FORMAT")

    def test_get_format_string(self):
        """Test format string generation"""
        # Regular UINT8
        field = M8Field("byte", 0, 0, 1, "UINT8")
        self.assertEqual(field.get_format_string(), "B")
        
        # Composite UINT4_2
        field = M8Field("upper|lower", 0, 0, 1, "UINT4_2")
        self.assertEqual(field.get_format_string(), "B")
        
        # Float
        field = M8Field("float", 0.0, 0, 4, "FLOAT32")
        self.assertEqual(field.get_format_string(), "<f")
        
        # String with dynamic length
        field = M8Field("string", "", 0, 5, "STRING")
        self.assertEqual(field.get_format_string(), "5s")
        
        field = M8Field("string", "", 0, 10, "STRING")
        self.assertEqual(field.get_format_string(), "10s")

    def test_part_operations(self):
        """Test operations on composite field parts"""
        field = M8Field("a|_", 0x50, 0, 1, "UINT4_2")  # 0x5 in upper, placeholder in lower
        
        self.assertTrue(field.is_composite)
        self.assertEqual(field.get_part_name(0), "a")
        self.assertEqual(field.get_part_name(1), "_")
        self.assertFalse(field.is_empty_part(0))
        self.assertTrue(field.is_empty_part(1))
        
        field = M8Field("_|b", 0x05, 0, 1, "UINT4_2")  # placeholder in upper, 0x5 in lower
        self.assertEqual(field.get_part_name(0), "_")
        self.assertEqual(field.get_part_name(1), "b")
        self.assertTrue(field.is_empty_part(0))
        self.assertFalse(field.is_empty_part(1))

    def test_read_write_value(self):
        """Test reading and writing values for fields"""
        # Test regular UINT8 field
        field = M8Field("byte", 0x42, 0, 1, "UINT8")
        data = bytearray([0x77])
        
        # Read value
        value = field.read_value(data)
        self.assertEqual(value, 0x77)
        
        # Write value
        field.write_value(data, 0x99)
        self.assertEqual(data[0], 0x99)
        
        # Test composite UINT4_2 field
        field = M8Field("upper|lower", 0x12, 0, 1, "UINT4_2")
        data = bytearray([0x53])  # 0x5 in upper, 0x3 in lower
        
        # Read upper nibble
        value = field.read_value(data, 0)
        self.assertEqual(value, 0x5)
        
        # Read lower nibble
        value = field.read_value(data, 1)
        self.assertEqual(value, 0x3)
        
        # Write upper nibble
        field.write_value(data, 0x8, 0)
        self.assertEqual(data[0], 0x83)  # 0x8 in upper, 0x3 in lower unchanged
        
        # Write lower nibble
        field.write_value(data, 0x7, 1)
        self.assertEqual(data[0], 0x87)  # 0x8 in upper unchanged, 0x7 in lower

    def test_get_set_typed_value(self):
        """Test getting and setting typed values"""
        # Test string field
        field = M8Field("text", "TEST", 0, 4, "STRING")
        data = bytearray(b'ABCD')
        
        # Read value
        value = field.get_typed_value(data)
        self.assertEqual(value, "ABCD")
        
        # Write value
        field.set_typed_value(data, "XYZ")
        self.assertEqual(data, b'XYZ\x00')  # Should be null-terminated
        
        # Test float field
        field = M8Field("float", 1.5, 0, 4, "FLOAT32")
        data = bytearray(4)
        
        # Write value
        field.set_typed_value(data, 2.5)
        
        # Read value
        value = field.get_typed_value(data)
        self.assertAlmostEqual(value, 2.5)
        
        # Test UINT8 field
        field = M8Field("byte", 0x42, 0, 1, "UINT8")
        data = bytearray([0])
        
        # Write and read value
        field.set_typed_value(data, 0x99)
        value = field.get_typed_value(data)
        self.assertEqual(value, 0x99)
        
        # Test composite UINT4_2 field parts
        field = M8Field("upper|lower", 0x12, 0, 1, "UINT4_2")
        data = bytearray([0])
        
        # Write and read upper part
        field.set_typed_value(data, 0x7, 0)
        value = field.get_typed_value(data, 0)
        self.assertEqual(value, 0x7)
        
        # Write and read lower part
        field.set_typed_value(data, 0x3, 1)
        value = field.get_typed_value(data, 1)
        self.assertEqual(value, 0x3)
        
        # Combined byte should have both parts
        self.assertEqual(data[0], 0x73)

    def test_check_default(self):
        """Test checking if field has default value"""
        # Test UINT8 field
        field = M8Field("byte", 0x42, 0, 1, "UINT8")
        data = bytearray([0x42])  # Default value
        self.assertTrue(field.check_default(data))
        
        data[0] = 0x43  # Non-default value
        self.assertFalse(field.check_default(data))
        
        # Test composite UINT4_2 field
        field = M8Field("upper|lower", 0x53, 0, 1, "UINT4_2")  # Default 0x5 in upper, 0x3 in lower
        data = bytearray([0x53])  # Default value
        
        # Upper nibble is default
        self.assertTrue(field.check_default(data, 0))
        
        # Lower nibble is default
        self.assertTrue(field.check_default(data, 1))
        
        data[0] = 0x63  # Changed upper nibble
        self.assertFalse(field.check_default(data, 0))
        self.assertTrue(field.check_default(data, 1))
        
        data[0] = 0x54  # Changed lower nibble
        self.assertTrue(field.check_default(data, 0))
        self.assertFalse(field.check_default(data, 1))
        
        # Test string field
        field = M8Field("text", "TEST", 0, 4, "STRING")
        data = bytearray(b'TEST')
        self.assertTrue(field.check_default(data))
        
        data = bytearray(b'TEMP')
        self.assertFalse(field.check_default(data))
        
        # Test float field
        field = M8Field("float", 1.5, 0, 4, "FLOAT32")
        data = bytearray(4)
        struct.pack_into("<f", data, 0, 1.5)
        self.assertTrue(field.check_default(data))
        
        struct.pack_into("<f", data, 0, 1.6)
        self.assertFalse(field.check_default(data))


class TestM8FieldMap(unittest.TestCase):
    def setUp(self):
        # Create a field map with one of each field type
        self.field_defs = [
            ("single_byte", 0x42, 0, 1, "UINT8"),
            ("upper|lower", 0x12, 1, 2, "UINT4_2"),
            ("floating", 1.5, 2, 6, "FLOAT32"),
            ("text", "TEST", 6, 10, "STRING")
        ]
        self.field_map = M8FieldMap(self.field_defs)

    def test_initialization(self):
        """Test field map initialization"""
        # Test regular fields
        self.assertTrue("single_byte" in self.field_map.fields)
        self.assertTrue("upper|lower" in self.field_map.fields)
        
        # Test parts of composite fields
        self.assertTrue("upper" in self.field_map.part_map)
        self.assertTrue("lower" in self.field_map.part_map)
        
        # Check part map entries
        self.assertEqual(self.field_map.part_map["upper"], ("upper|lower", 0))
        self.assertEqual(self.field_map.part_map["lower"], ("upper|lower", 1))

    def test_get_field(self):
        """Test getting fields by name"""
        # Get regular field
        field, part_index = self.field_map.get_field("single_byte")
        self.assertEqual(field.name, "single_byte")
        self.assertIsNone(part_index)
        
        # Get composite field
        field, part_index = self.field_map.get_field("upper|lower")
        self.assertEqual(field.name, "upper|lower")
        self.assertIsNone(part_index)
        
        # Get part of composite field
        field, part_index = self.field_map.get_field("upper")
        self.assertEqual(field.name, "upper|lower")
        self.assertEqual(part_index, 0)
        
        field, part_index = self.field_map.get_field("lower")
        self.assertEqual(field.name, "upper|lower")
        self.assertEqual(part_index, 1)
        
        # Test non-existent field
        with self.assertRaises(AttributeError):
            self.field_map.get_field("non_existent")

    def test_has_field(self):
        """Test checking if field exists"""
        # Regular fields
        self.assertTrue(self.field_map.has_field("single_byte"))
        self.assertTrue(self.field_map.has_field("floating"))
        self.assertTrue(self.field_map.has_field("text"))
        
        # Composite field and parts
        self.assertTrue(self.field_map.has_field("upper|lower"))
        self.assertTrue(self.field_map.has_field("upper"))
        self.assertTrue(self.field_map.has_field("lower"))
        
        # Non-existent fields
        self.assertFalse(self.field_map.has_field("non_existent"))

    def test_max_offset(self):
        """Test getting maximum byte offset"""
        self.assertEqual(self.field_map.max_offset(), 10)
        
        # Add a field with larger offset
        field_defs = self.field_defs + [("extra", 0, 10, 15, "STRING")]
        field_map = M8FieldMap(field_defs)
        self.assertEqual(field_map.max_offset(), 15)

    def test_get_default_byte_at(self):
        """Test getting default byte value at offset"""
        # UINT8 field
        self.assertEqual(self.field_map.get_default_byte_at(0), 0x42)
        
        # UINT4_2 field
        self.assertEqual(self.field_map.get_default_byte_at(1), 0x12)
        
        # FLOAT32 field (more complex, just verify it's not None)
        self.assertIsNotNone(self.field_map.get_default_byte_at(2))
        self.assertIsNotNone(self.field_map.get_default_byte_at(3))
        self.assertIsNotNone(self.field_map.get_default_byte_at(4))
        self.assertIsNotNone(self.field_map.get_default_byte_at(5))
        
        # STRING field
        self.assertEqual(self.field_map.get_default_byte_at(6), ord('T'))
        self.assertEqual(self.field_map.get_default_byte_at(7), ord('E'))
        self.assertEqual(self.field_map.get_default_byte_at(8), ord('S'))
        self.assertEqual(self.field_map.get_default_byte_at(9), ord('T'))


if __name__ == '__main__':
    unittest.main()
