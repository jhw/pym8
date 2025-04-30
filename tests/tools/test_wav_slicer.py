import unittest
import os
import tempfile
import shutil
import wave
import struct
from unittest.mock import patch, mock_open, MagicMock

from m8.tools.wav_slicer import WAVSlicer


class TestWAVSlicer(unittest.TestCase):
    def setUp(self):
        """Set up temporary directory and test WAV file."""
        # Create temp dir in project root
        tmp_root = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "tmp")
        os.makedirs(tmp_root, exist_ok=True)
        self.temp_dir = os.path.join(tmp_root, f"test_slice_wav_{os.getpid()}")
        os.makedirs(self.temp_dir, exist_ok=True)
        
        # Create a simple test WAV file
        self.input_wav = os.path.join(self.temp_dir, "test.wav")
        self.create_test_wav(self.input_wav)
    
    def tearDown(self):
        """Clean up temporary files."""
        shutil.rmtree(self.temp_dir)
    
    def create_test_wav(self, filename, num_frames=48000):
        """Create a simple test WAV file."""
        with wave.open(filename, 'wb') as wav:
            wav.setnchannels(2)
            wav.setsampwidth(2)
            wav.setframerate(48000)
            
            # Create a simple sine wave (just zeroes for testing)
            data = bytes([0] * (num_frames * 4))  # 2 channels * 2 bytes per sample
            wav.writeframes(data)
    
    def test_create_slice_points(self):
        """Test create_slice_points method."""
        slicer = WAVSlicer(num_slices=4)
        # Test with 1000 frames
        slice_points = slicer.create_slice_points(1000)
        self.assertEqual(len(slice_points), 4)
        self.assertEqual(slice_points, [0, 250, 500, 750])
        
        # Test with zero slices
        slicer = WAVSlicer(num_slices=0)
        slice_points = slicer.create_slice_points(1000)
        self.assertEqual(len(slice_points), 0)
        
        # Test with negative slices (should return empty)
        slicer = WAVSlicer(num_slices=-1)
        slice_points = slicer.create_slice_points(1000)
        self.assertEqual(len(slice_points), 0)
    
    def test_create_standard_cue_chunk(self):
        """Test create_standard_cue_chunk method."""
        slicer = WAVSlicer()
        
        # Test with 3 slice points
        slice_points = [0, 100, 200]
        cue_chunk = slicer.create_standard_cue_chunk(slice_points)
        
        # Verify chunk header is 'cue '
        self.assertEqual(cue_chunk[:4], b'cue ')
        
        # Unpack chunk size (4 bytes after header)
        chunk_size = struct.unpack('<I', cue_chunk[4:8])[0]
        
        # Verify chunk data length matches expectation
        # 4 bytes for numCuePoints + (24 bytes per cue point * 3 points)
        expected_size = 4 + (24 * 3)
        self.assertEqual(chunk_size, expected_size)
        
        # Verify number of cue points
        num_cues = struct.unpack('<I', cue_chunk[8:12])[0]
        self.assertEqual(num_cues, 3)
        
        # Verify first cue point (ID should be 1)
        cue_id = struct.unpack('<I', cue_chunk[12:16])[0]
        self.assertEqual(cue_id, 1)
        
        # Verify the data chunk ID is 'data'
        self.assertEqual(cue_chunk[20:24], b'data')
    
    def test_create_m8_atad_cue_chunk(self):
        """Test create_m8_atad_cue_chunk method."""
        slicer = WAVSlicer()
        
        # Test with 3 slice points
        slice_points = [0, 100, 200]
        cue_chunk = slicer.create_m8_atad_cue_chunk(slice_points)
        
        # Verify chunk header is 'cue '
        self.assertEqual(cue_chunk[:4], b'cue ')
        
        # Unpack chunk size (4 bytes after header)
        chunk_size = struct.unpack('<I', cue_chunk[4:8])[0]
        
        # Verify chunk data length matches expectation
        # 4 bytes for numCuePoints + (24 bytes per cue point * 3 points)
        expected_size = 4 + (24 * 3)
        self.assertEqual(chunk_size, expected_size)
        
        # Verify number of cue points
        num_cues = struct.unpack('<I', cue_chunk[8:12])[0]
        self.assertEqual(num_cues, 3)
        
        # Verify first cue point (ID should be 0 for M8 format)
        cue_id = struct.unpack('<I', cue_chunk[12:16])[0]
        self.assertEqual(cue_id, 0)
        
        # Verify the data chunk ID is 'atad' (reversed 'data')
        self.assertEqual(cue_chunk[20:24], b'atad')
    
    def test_process_wav_file(self):
        """Test process_wav_file with actual file IO."""
        slicer = WAVSlicer(num_slices=8)
        
        # Process the test file
        output_file = slicer.process_wav_file(self.input_wav)
        
        # Verify output file exists
        self.assertTrue(os.path.exists(output_file))
        
        # Read the output file
        with open(output_file, 'rb') as f:
            data = f.read()
        
        # Verify it's a valid RIFF/WAVE file
        self.assertEqual(data[:4], b'RIFF')
        self.assertEqual(data[8:12], b'WAVE')
        
        # Verify it contains a standard cue chunk
        self.assertIn(b'cue ', data)
        
        # Verify it contains an M8 'atad' cue chunk
        atad_pos = data.find(b'atad')
        self.assertGreater(atad_pos, 0)
    
    def test_file_not_found(self):
        """Test process_wav_file with non-existent file."""
        slicer = WAVSlicer()
        
        with self.assertRaises(FileNotFoundError):
            slicer.process_wav_file(os.path.join(self.temp_dir, "nonexistent.wav"))
    
    def test_not_a_wav_file(self):
        """Test process_wav_file with non-WAV file."""
        # Create a non-WAV file
        non_wav = os.path.join(self.temp_dir, "not_a_wav.txt")
        with open(non_wav, 'wb') as f:
            f.write(b'This is not a WAV file')
        
        slicer = WAVSlicer()
        with self.assertRaises(RuntimeError):
            slicer.process_wav_file(non_wav)
    
    def test_zero_slices(self):
        """Test process_wav_file with zero slices."""
        slicer = WAVSlicer(num_slices=0)
        
        with self.assertRaises(RuntimeError):
            slicer.process_wav_file(self.input_wav)
    
    def test_class_method_slice_file(self):
        """Test the class method slice_file."""
        # Use class method for simpler API
        output_file = WAVSlicer.slice_file(self.input_wav, num_slices=4)
        
        # Verify output file exists
        self.assertTrue(os.path.exists(output_file))
        
        # Verify output filename contains slice count
        self.assertIn("-4slices", output_file)
        
        # Read the output file to verify it contains cue points
        with open(output_file, 'rb') as f:
            data = f.read()
        
        # Verify it contains cue chunks
        self.assertIn(b'cue ', data)
        self.assertIn(b'atad', data)


if __name__ == '__main__':
    unittest.main()
