import unittest
from m8 import M8Block, NULL
from m8.core.list import m8_list_class
from m8.core.object import m8_object_class

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
            row_class=self.TestRowClass
        )

    def test_initialization(self):
        """Test list initialization"""
        m8_list = self.TestClass()
        self.assertEqual(len(m8_list), 3)
        self.assertIsInstance(m8_list[0], self.TestRowClass)

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
            row_class_resolver=resolver
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

if __name__ == '__main__':
    unittest.main()
