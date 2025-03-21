import unittest
import struct
from m8.api.metadata import M8Metadata

class TestM8Metadata(unittest.TestCase):
    def test_read_from_binary(self):
        # Create test binary data
        test_data = bytearray()
        
        # Directory: "/Songs/" (128 bytes)
        directory = "/Songs/"
        dir_bytes = directory.encode('utf-8')
        test_data.extend(dir_bytes)
        test_data.extend(bytes([0] * (128 - len(dir_bytes))))
        
        # Transpose: 2 (1 byte)
        test_data.append(2)
        
        # Tempo: 140.5 (4 bytes, float32)
        test_data.extend(struct.pack('<f', 140.5))
        
        # Quantize: 4 (1 byte)
        test_data.append(4)
        
        # Name: "TEST SONG" (12 bytes)
        name = "TEST SONG"
        name_bytes = name.encode('utf-8')
        test_data.extend(name_bytes)
        test_data.extend(bytes([0] * (12 - len(name_bytes))))
        
        # Key: 3 (1 byte)
        test_data.append(3)
        
        # Read metadata from binary
        metadata = M8Metadata.read(test_data)
        
        # Assert values were read correctly
        self.assertEqual(metadata.directory, "/Songs/")
        self.assertEqual(metadata.transpose, 2)
        self.assertAlmostEqual(metadata.tempo, 140.5, places=4)
        self.assertEqual(metadata.quantize, 4)
        self.assertEqual(metadata.name, "TEST SONG")
        self.assertEqual(metadata.key, 3)
        
    def test_read_with_null_terminated_strings(self):
        # Test with strings that have null bytes before their max length
        test_data = bytearray()
        
        # Directory: "/Songs" with early null termination (128 bytes)
        directory = "/Songs"
        dir_bytes = directory.encode('utf-8')
        test_data.extend(dir_bytes)
        test_data.extend(bytes([0] * (128 - len(dir_bytes))))
        
        # Rest of the values
        test_data.append(0)  # transpose
        test_data.extend(struct.pack('<f', 120.0))  # tempo
        test_data.append(0)  # quantize
        
        # Name with early null termination
        name = "SHORT"
        name_bytes = name.encode('utf-8')
        test_data.extend(name_bytes)
        test_data.extend(bytes([0] * (12 - len(name_bytes))))
        
        test_data.append(0)  # key
        
        # Read metadata from binary
        metadata = M8Metadata.read(test_data)
        
        # Assert null termination was handled correctly
        self.assertEqual(metadata.directory, "/Songs")
        self.assertEqual(metadata.name, "SHORT")
    
    def test_write_to_binary(self):
        # Create metadata with specific values
        metadata = M8Metadata(
            directory="/Projects/",
            transpose=1,
            tempo=130.25,
            quantize=2,
            name="BINARY TEST",
            key=5
        )
        
        # Write to binary
        binary = metadata.write()
        
        # Verify the binary has the correct size
        self.assertEqual(len(binary), M8Metadata.BLOCK_SIZE)
        
        # Parse it back manually to verify
        # Directory (null-terminated)
        dir_bytes = binary[M8Metadata.DIRECTORY_OFFSET:M8Metadata.DIRECTORY_OFFSET + M8Metadata.DIRECTORY_LENGTH]
        null_idx = dir_bytes.find(0)
        if null_idx != -1:
            dir_bytes = dir_bytes[:null_idx]
        directory = dir_bytes.decode('utf-8')
        self.assertEqual(directory, "/Projects/")
        
        # Transpose
        transpose = binary[M8Metadata.TRANSPOSE_OFFSET]
        self.assertEqual(transpose, 1)
        
        # Tempo
        tempo = struct.unpack('<f', binary[M8Metadata.TEMPO_OFFSET:M8Metadata.TEMPO_OFFSET + M8Metadata.TEMPO_SIZE])[0]
        self.assertAlmostEqual(tempo, 130.25, places=4)
        
        # Quantize
        quantize = binary[M8Metadata.QUANTIZE_OFFSET]
        self.assertEqual(quantize, 2)
        
        # Name
        name_bytes = binary[M8Metadata.NAME_OFFSET:M8Metadata.NAME_OFFSET + M8Metadata.NAME_LENGTH]
        null_idx = name_bytes.find(0)
        if null_idx != -1:
            name_bytes = name_bytes[:null_idx]
        name = name_bytes.decode('utf-8')
        self.assertEqual(name, "BINARY TEST")
        
        # Key
        key = binary[M8Metadata.KEY_OFFSET]
        self.assertEqual(key, 5)
    
    def test_read_write_consistency(self):
        # Test binary serialization/deserialization consistency
        test_cases = [
            # directory, transpose, tempo, quantize, name, key
            ("/Songs/", 0, 120.0, 0, "TEST1", 0),
            ("/Projects/MyProj/", 3, 145.75, 2, "COMPLEX", 7),
            ("/", 15, 60.0, 7, "MINIMAL", 15),
            # Test max length names and directories
            ("/very/long/directory/path/that/will/be/truncated/", 5, 100.0, 3, "LONG NAME T", 2)
        ]
        
        for directory, transpose, tempo, quantize, name, key in test_cases:
            # Create a metadata object
            original = M8Metadata(
                directory=directory,
                transpose=transpose,
                tempo=tempo,
                quantize=quantize,
                name=name,
                key=key
            )
            
            # Serialize to binary
            binary = original.write()
            
            # Deserialize from binary
            deserialized = M8Metadata.read(binary)
            
            # Verify all properties match
            # For directory and name, we need to account for potential truncation
            expected_dir = directory
            if len(directory.encode('utf-8')) > M8Metadata.DIRECTORY_LENGTH - 1:
                # Directory would be truncated
                trimmed_bytes = directory.encode('utf-8')[:M8Metadata.DIRECTORY_LENGTH - 1]
                expected_dir = trimmed_bytes.decode('utf-8', errors='replace')
            
            expected_name = name
            if len(name.encode('utf-8')) > M8Metadata.NAME_LENGTH - 1:
                # Name would be truncated
                trimmed_bytes = name.encode('utf-8')[:M8Metadata.NAME_LENGTH - 1]
                expected_name = trimmed_bytes.decode('utf-8', errors='replace')
            
            self.assertEqual(deserialized.directory, expected_dir)
            self.assertEqual(deserialized.transpose, original.transpose)
            self.assertAlmostEqual(deserialized.tempo, original.tempo, places=4)
            self.assertEqual(deserialized.quantize, original.quantize)
            self.assertEqual(deserialized.name, expected_name)
            self.assertEqual(deserialized.key, original.key)
    
    def test_constructor_and_defaults(self):
        # Test default constructor
        metadata = M8Metadata()
        self.assertEqual(metadata.directory, "/Songs/")
        self.assertEqual(metadata.transpose, 0)
        self.assertEqual(metadata.tempo, 120.0)
        self.assertEqual(metadata.quantize, 0)
        self.assertEqual(metadata.name, "HELLO")
        self.assertEqual(metadata.key, 0)
        
        # Test constructor with arguments
        metadata = M8Metadata(
            directory="/Custom/",
            transpose=3,
            tempo=140.0,
            quantize=2,
            name="CUSTOM",
            key=5
        )
        self.assertEqual(metadata.directory, "/Custom/")
        self.assertEqual(metadata.transpose, 3)
        self.assertEqual(metadata.tempo, 140.0)
        self.assertEqual(metadata.quantize, 2)
        self.assertEqual(metadata.name, "CUSTOM")
        self.assertEqual(metadata.key, 5)
        
        # Test constructor with partial arguments
        metadata = M8Metadata(directory="/Partial/", name="PARTIAL")
        self.assertEqual(metadata.directory, "/Partial/")
        self.assertEqual(metadata.transpose, 0)  # Default
        self.assertEqual(metadata.tempo, 120.0)  # Default
        self.assertEqual(metadata.quantize, 0)  # Default
        self.assertEqual(metadata.name, "PARTIAL")
        self.assertEqual(metadata.key, 0)  # Default
    
    def test_is_empty(self):
        # Test is_empty method
        # Empty metadata should have empty directory and name
        self.assertTrue(M8Metadata(directory="", name="").is_empty())
        self.assertTrue(M8Metadata(directory="/", name="").is_empty())
        self.assertTrue(M8Metadata(directory="", name=" ").is_empty())
        
        # Non-empty cases
        self.assertFalse(M8Metadata(directory="/Songs/", name="").is_empty())
        self.assertFalse(M8Metadata(directory="", name="SONG").is_empty())
        self.assertFalse(M8Metadata(directory="/Songs/", name="SONG").is_empty())
    
    def test_clone(self):
        # Test clone method
        original = M8Metadata(
            directory="/Clone/",
            transpose=4,
            tempo=125.5,
            quantize=3,
            name="ORIGINAL",
            key=2
        )
        clone = original.clone()
        
        # Verify clone has the same values
        self.assertEqual(clone.directory, original.directory)
        self.assertEqual(clone.transpose, original.transpose)
        self.assertEqual(clone.tempo, original.tempo)
        self.assertEqual(clone.quantize, original.quantize)
        self.assertEqual(clone.name, original.name)
        self.assertEqual(clone.key, original.key)
        
        # Verify clone is a different object
        self.assertIsNot(clone, original)
        
        # Modify clone and verify original remains unchanged
        clone.name = "MODIFIED"
        clone.tempo = 150.0
        self.assertEqual(original.name, "ORIGINAL")
        self.assertEqual(original.tempo, 125.5)
    
    def test_as_dict(self):
        # Test as_dict method
        metadata = M8Metadata(
            directory="/Dict/",
            transpose=6,
            tempo=133.25,
            quantize=4,
            name="DICT TEST",
            key=7
        )
        
        result_dict = metadata.as_dict()
        
        # Verify dictionary contains all expected fields with correct values
        self.assertEqual(result_dict["directory"], "/Dict/")
        self.assertEqual(result_dict["transpose"], 6)
        self.assertEqual(result_dict["tempo"], 133.25)
        self.assertEqual(result_dict["quantize"], 4)
        self.assertEqual(result_dict["name"], "DICT TEST")
        self.assertEqual(result_dict["key"], 7)
        
        # Verify dictionary contains exactly the expected fields
        expected_keys = {"directory", "transpose", "tempo", "quantize", "name", "key"}
        self.assertEqual(set(result_dict.keys()), expected_keys)
    
    def test_from_dict(self):
        # Test from_dict method
        # Complete dictionary
        data = {
            "directory": "/FromDict/",
            "transpose": 8,
            "tempo": 142.75,
            "quantize": 5,
            "name": "FROM DICT",
            "key": 9
        }
        metadata = M8Metadata.from_dict(data)
        
        self.assertEqual(metadata.directory, "/FromDict/")
        self.assertEqual(metadata.transpose, 8)
        self.assertEqual(metadata.tempo, 142.75)
        self.assertEqual(metadata.quantize, 5)
        self.assertEqual(metadata.name, "FROM DICT")
        self.assertEqual(metadata.key, 9)
        
        # Test deserializing and serializing via dictionary roundtrip
        original = M8Metadata(
            directory="/Original/",
            transpose=1,
            tempo=118.5,
            quantize=3,
            name="ROUNDTRIP",
            key=4
        )
        
        # Convert to dict and back
        dict_data = original.as_dict()
        roundtrip = M8Metadata.from_dict(dict_data)
        
        # Verify all properties match
        self.assertEqual(roundtrip.directory, original.directory)
        self.assertEqual(roundtrip.transpose, original.transpose)
        self.assertEqual(roundtrip.tempo, original.tempo)
        self.assertEqual(roundtrip.quantize, original.quantize)
        self.assertEqual(roundtrip.name, original.name)
        self.assertEqual(roundtrip.key, original.key)

if __name__ == '__main__':
    unittest.main()