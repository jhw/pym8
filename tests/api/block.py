"""Tests for M8Block — the raw-bytes fallback used for unparsed slots."""
import unittest

from m8.api import M8Block


class TestM8Block(unittest.TestCase):
    def test_read(self):
        block = M8Block.read(b"\x01\x02\x03\x04")
        self.assertEqual(block.data, bytearray(b"\x01\x02\x03\x04"))

    def test_write(self):
        block = M8Block()
        block.data = bytearray(b"\x01\x02\x03\x04")
        self.assertEqual(block.write(), bytearray(b"\x01\x02\x03\x04"))

    def test_as_dict(self):
        block = M8Block()
        block.data = bytearray(b"\x01\x02\x03")
        self.assertEqual(block.as_dict(), {"data": [1, 2, 3]})

    def test_from_dict(self):
        block = M8Block.from_dict({"data": [1, 2, 3]})
        self.assertEqual(block.data, bytearray(b"\x01\x02\x03"))

    def test_from_dict_empty(self):
        block = M8Block.from_dict({})
        self.assertEqual(block.data, bytearray())


if __name__ == "__main__":
    unittest.main()
