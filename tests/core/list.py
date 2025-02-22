from m8 import M8Block, NULL
from m8.core.list import m8_list_class
from m8.core.object import m8_object_class

import unittest

class TestM8List(unittest.TestCase):
    def setUp(self):
        """Create test row and list classes"""
        self.TestRowClass = m8_object_class([
            ("type", 0x00, 0, 1, "UINT8"),
            ("value", 0x42, 1, 2, "UINT8")
        ])
        self.TestClass = m8_list_class(
            row_size=2,
            row_count=3,
            row_class=self.TestRowClass,
            default_byte=NULL  # Add the default_byte parameter
        )
        
    def test_initialization(self):
        """Test list initialization"""
        m8_list = self.TestClass()
        self.assertEqual(len(m8_list), 3)
        self.assertIsInstance(m8_list[0], self.TestRowClass)

    def test_initialization_with_items(self):
        """Test list initialization with custom items"""
        # Create custom items
        item1 = self.TestRowClass()
        item1.value = 0xFF
        
        item2 = self.TestRowClass()
        item2.value = 0xEE
    
        # Initialize list with items
        m8_list = self.TestClass(items=[item1, item2])
    
        # Check that items were properly added
        self.assertEqual(len(m8_list), 3)  # Should still have ROW_COUNT items
        self.assertEqual(m8_list[0].value, 0xFF)
        self.assertEqual(m8_list[1].value, 0xEE)
        self.assertEqual(m8_list[2].value, 0x42)  # Default value for the auto-created item
    
        # Test with too many items
        with self.assertRaises(ValueError):
            self.TestClass(items=[item1, item1, item1, item1])  # ROW_COUNT is 3
        
    def test_row_access(self):
        """Test row access and modification"""
        m8_list = self.TestClass()
        m8_list[0].value = 0xFF
        
        self.assertEqual(m8_list[0].value, 0xFF)
        self.assertEqual(m8_list[1].value, 0x42)  # Default
        
    def test_data_persistence(self):
        """Test write/read cycle preserves data"""
        list1 = self.TestClass()
        list1[0].value = 0xFF
        list1[1].value = 0xEE
        
        data = list1.write()
        list2 = self.TestClass.read(data)
        
        self.assertEqual(list2[0].value, 0xFF)
        self.assertEqual(list2[1].value, 0xEE)
        
    def test_empty_check(self):
        """Test is_empty() functionality"""
        m8_list = self.TestClass()
        
        # Set a non-default value
        m8_list[0].value = 0xFF
        self.assertFalse(m8_list.is_empty())
        
        # Set to empty M8Blocks
        for i in range(3):
            m8_list[i] = M8Block()
        self.assertTrue(m8_list.is_empty())
        
    def test_row_resolution(self):
        """Test row class resolution"""
        AltRowClass = m8_object_class([
            ("type", 0x01, 0, 1, "UINT8"),
            ("data", 0x00, 1, 2, "UINT8")
        ])
        def resolver(data):
            return AltRowClass if data[0] == 0x01 else self.TestRowClass
        DynamicList = m8_list_class(
            row_size=2,
            row_count=2,
            row_class=self.TestRowClass,
            row_class_resolver=resolver,
            default_byte=NULL
        )
        # Test resolution with mixed data
        data = bytes([0x00, 0xFF, 0x01, 0xFF])
        dynamic_list = DynamicList.read(data)
        
        self.assertIsInstance(dynamic_list[0], self.TestRowClass)
        self.assertIsInstance(dynamic_list[1], AltRowClass)
        
    def test_clone(self):
        """Test list cloning"""
        list1 = self.TestClass()
        list1[0].value = 0xFF
        
        list2 = list1.clone()
        list2[0].value = 0xEE
        
        self.assertEqual(list1[0].value, 0xFF)
        self.assertEqual(list2[0].value, 0xEE)
        
    def test_write_padding(self):
        """Test that write() correctly pads rows to ROW_SIZE"""
        # Create a mock row class that returns less than ROW_SIZE bytes
        class ShortRow:
            def write(self):
                return bytes([0xAA])  # Only 1 byte
        
        # Create a list with one short row
        m8_list = self.TestClass()
        m8_list[0] = ShortRow()
        
        data = m8_list.write()
        
        # Should be padded to ROW_SIZE
        self.assertEqual(data[0:2], bytes([0xAA, NULL]))
        
        # Total size should be ROW_SIZE * ROW_COUNT
        self.assertEqual(len(data), 2 * 3)
        
    def test_write_truncation(self):
        """Test that write() correctly truncates rows to ROW_SIZE"""
        # Create a mock row class that returns more than ROW_SIZE bytes
        class LongRow:
            def write(self):
                return bytes([0xBB, 0xCC, 0xDD])  # 3 bytes
        
        # Create a list with one long row
        m8_list = self.TestClass()
        m8_list[0] = LongRow()
        
        data = m8_list.write()
        
        # Should be truncated to ROW_SIZE
        self.assertEqual(data[0:2], bytes([0xBB, 0xCC]))
        
        # Total size should be ROW_SIZE * ROW_COUNT
        self.assertEqual(len(data), 2 * 3)
        
    def test_default_byte(self):
        """Test that default_byte parameter is used for padding"""
        # Create a class with a specific default_byte
        CustomDefaultClass = m8_list_class(
            row_size=2,
            row_count=3,
            row_class=self.TestRowClass,
            default_byte=0xFF  # Use 0xFF for padding
        )
        
        # Create a mock row that returns less than ROW_SIZE
        class ShortRow:
            def write(self):
                return bytes([0xAA])  # Only 1 byte
        
        # Create a list with the custom default
        m8_list = CustomDefaultClass()
        m8_list[0] = ShortRow()
        
        data = m8_list.write()
        
        # Should be padded with 0xFF
        self.assertEqual(data[0:2], bytes([0xAA, 0xFF]))
        
if __name__ == '__main__':
    unittest.main()
