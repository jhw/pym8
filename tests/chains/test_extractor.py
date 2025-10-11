import unittest
import os
import tempfile
import shutil
import wave
import struct

from m8.chains.extractor import M8ChainExtractor
from m8.chains.slicer import M8ChainSlicer


class TestM8ChainExtractor(unittest.TestCase):
    def setUp(self):
        """Set up temporary directory and test WAV files."""
        # Create temp dir in project root
        tmp_root = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "tmp")
        os.makedirs(tmp_root, exist_ok=True)
        self.temp_dir = os.path.join(tmp_root, f"test_extract_slices_{os.getpid()}")
        os.makedirs(self.temp_dir, exist_ok=True)
        
        # Create a simple test WAV file
        self.input_wav = os.path.join(self.temp_dir, "test.wav")
        self.create_test_wav(self.input_wav, num_frames=48000)
        
        # Create sliced WAV files with different slice counts
        self.slicer = M8ChainSlicer(num_slices=4)
        self.sliced_wav = self.slicer.process_wav_file(self.input_wav)

        self.slicer8 = M8ChainSlicer(num_slices=8)
        self.sliced_wav8 = self.slicer8.process_wav_file(self.input_wav)
        
        # Create empty WAV for error testing
        self.empty_wav = os.path.join(self.temp_dir, "empty.wav")
        self.create_test_wav(self.empty_wav, num_frames=0)
    
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
    
    def test_extract_slices(self):
        """Test basic slice extraction from file."""
        extractor = M8ChainExtractor()
        slices = extractor.extract_slices(self.sliced_wav)
        
        # Should have 4 slices
        self.assertEqual(len(slices), 4)
        
        # Check the structure of returned slices
        for start, end in slices:
            self.assertIsInstance(start, int)
            self.assertIsInstance(end, int)
            self.assertLess(start, end)
        
        # Verify the first slice starts at 0
        self.assertEqual(slices[0][0], 0)
        
        # Check if the slice points are evenly spaced
        intervals = []
        prev_start = None
        for start, _ in slices:
            if prev_start is not None:
                intervals.append(start - prev_start)
            prev_start = start
        
        # All intervals should be equal for evenly spaced slices
        if intervals:
            self.assertEqual(len(set(intervals)), 1)
    
    def test_extract_slices_from_bytes(self):
        """Test slice extraction from binary data."""
        # Read the file as bytes
        with open(self.sliced_wav, 'rb') as f:
            wav_data = f.read()

        extractor = M8ChainExtractor()
        slices = extractor.extract_slices_from_bytes(wav_data)
        
        # Should have 4 slices
        self.assertEqual(len(slices), 4)
    
    def test_class_method_extract_with_path(self):
        """Test class method extract with file path."""
        slices = M8ChainExtractor.extract(self.sliced_wav)
        
        # Should have 4 slices
        self.assertEqual(len(slices), 4)
    
    def test_class_method_extract_with_bytes(self):
        """Test class method extract with binary data."""
        # Read the file as bytes
        with open(self.sliced_wav, 'rb') as f:
            wav_data = f.read()

        slices = M8ChainExtractor.extract(wav_data)
        
        # Should have 4 slices
        self.assertEqual(len(slices), 4)
    
    def test_extract_different_slice_counts(self):
        """Test extraction with different slice counts."""
        # Extract from 8-slice WAV
        slices = M8ChainExtractor.extract(self.sliced_wav8)
        
        # Should have 8 slices
        self.assertEqual(len(slices), 8)
        
        # Check if slice ranges cover the whole file
        self.assertEqual(slices[0][0], 0)
        with wave.open(self.sliced_wav8, 'rb') as wav:
            self.assertEqual(slices[-1][1], wav.getnframes())
    
    def test_invalid_file(self):
        """Test with an invalid file."""
        # Create a non-WAV file
        non_wav = os.path.join(self.temp_dir, "not_a_wav.txt")
        with open(non_wav, 'wb') as f:
            f.write(b'This is not a WAV file')
        
        with self.assertRaises(ValueError):
            M8ChainExtractor.extract(non_wav)
    
    def test_file_with_no_slices(self):
        """Test with a WAV file that has no slices."""
        with self.assertRaises(ValueError):
            M8ChainExtractor.extract(self.input_wav)  # Original unsliced WAV
    
    def test_skip_zero_length_slices(self):
        """Test that zero-length slices are skipped."""
        # Create a WAV with slices where some have the same start/end
        # First, read the sliced file
        with open(self.sliced_wav, 'rb') as f:
            data = f.read()
        
        # Find the cue chunk
        cue_pos = data.find(b'cue ')
        if cue_pos > 0:
            # Modify the cue chunk to make two consecutive slices have the same position
            # This is 24 bytes per cue point, with the sample offset at position 20
            # Get num_cues first
            num_cues_pos = cue_pos + 8
            num_cues = struct.unpack('<I', data[num_cues_pos:num_cues_pos+4])[0]
            
            if num_cues >= 2:
                # Get the sample offset of the first cue point
                cue_data_pos = num_cues_pos + 4
                sample_offset_pos_1 = cue_data_pos + 20
                sample_offset_1 = struct.unpack('<I', data[sample_offset_pos_1:sample_offset_pos_1+4])[0]
                
                # Set the second cue point to the same offset (creating a zero-length slice)
                sample_offset_pos_2 = cue_data_pos + 24 + 20
                
                # Create modified data by patching the second sample offset
                modified_data = bytearray(data)
                modified_data[sample_offset_pos_2:sample_offset_pos_2+4] = struct.pack('<I', sample_offset_1)
                
                # Write to a new test file
                modified_wav = os.path.join(self.temp_dir, "modified_slices.wav")
                with open(modified_wav, 'wb') as f:
                    f.write(modified_data)
                
                # Now extract slices and verify we don't have the zero-length one
                slices = M8ChainExtractor.extract(modified_wav)
                
                # Should have fewer slices than original
                self.assertLess(len(slices), num_cues)
                
                # Verify no zero-length slices
                for start, end in slices:
                    self.assertLess(start, end, "Found a slice with zero length")


if __name__ == '__main__':
    unittest.main()
