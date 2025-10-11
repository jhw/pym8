import unittest
import os
import tempfile
import shutil
import wave
import struct
from pathlib import Path
from pydub import AudioSegment

from m8.chains.builder import M8ChainBuilder
from m8.chains.extractor import M8ChainExtractor


class TestM8ChainBuilder(unittest.TestCase):
    def setUp(self):
        """Set up temporary directory and test WAV files."""
        # Create temp dir in project root
        tmp_root = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "tmp")
        os.makedirs(tmp_root, exist_ok=True)
        self.temp_dir = os.path.join(tmp_root, f"test_chain_builder_{os.getpid()}")
        os.makedirs(self.temp_dir, exist_ok=True)
        
        # Create test packs directory
        self.packs_dir = os.path.join(self.temp_dir, "packs")
        os.makedirs(self.packs_dir, exist_ok=True)
        
        # Create pack directories and sample files
        self.pack_names = ["pack1", "pack2"]
        self.file_names = ["kick.wav", "snare.wav", "hat.wav"]
        
        self.test_files = []
        for pack in self.pack_names:
            pack_dir = os.path.join(self.packs_dir, pack)
            os.makedirs(pack_dir, exist_ok=True)
            
            for file_name in self.file_names:
                file_path = os.path.join(pack_dir, file_name)
                self.create_test_wav(file_path)
                self.test_files.append(file_path)
    
    def tearDown(self):
        """Clean up temporary files."""
        shutil.rmtree(self.temp_dir)
    
    def create_test_wav(self, filename, duration_ms=500, sample_rate=44100):
        """Create a simple test WAV file."""
        # Create a silent audio segment
        segment = AudioSegment.silent(duration=duration_ms, frame_rate=sample_rate)
        
        # Export as WAV
        segment.export(filename, format="wav")
    
    def test_init(self):
        """Test constructor with various parameters."""
        # Default initialization
        chain_builder = M8ChainBuilder(500, 10)
        self.assertEqual(chain_builder.duration_ms, 500)
        self.assertEqual(chain_builder.fade_ms, 10)
        self.assertEqual(chain_builder.packs_dir, Path("tmp/packs"))

        # Custom packs directory
        chain_builder = M8ChainBuilder(500, 10, packs_dir=self.packs_dir)
        self.assertEqual(chain_builder.packs_dir, Path(self.packs_dir))
    
    def test_build_chain_from_files(self):
        """Test building a chain from file paths."""
        chain_builder = M8ChainBuilder(500, 10)
        
        # Use a subset of test files
        files_to_use = self.test_files[:3]
        
        # Build chain
        chain, name_to_index, slice_positions = chain_builder.build_chain_from_files(files_to_use)
        
        # Check chain type
        self.assertIsInstance(chain, AudioSegment)
        
        # Check duration
        expected_duration = 500 * len(files_to_use)
        self.assertEqual(len(chain), expected_duration)
        
        # Check mapping and slice positions
        self.assertEqual(len(name_to_index), len(files_to_use))
        self.assertEqual(len(slice_positions), len(files_to_use) + 1)
        
        # Check that slice positions are evenly spaced
        intervals = []
        for i in range(1, len(slice_positions)):
            intervals.append(slice_positions[i] - slice_positions[i-1])
        
        # All intervals should be equal for evenly spaced slices
        self.assertEqual(len(set(intervals)), 1)
    
    def test_build_chain(self):
        """Test building a chain from sample dictionaries."""
        chain_builder = M8ChainBuilder(500, 10, packs_dir=self.packs_dir)
        
        # Create sample dictionaries
        samples = []
        for i, file_path in enumerate(self.test_files[:3]):
            path = Path(file_path)
            pack_name = path.parent.name
            file_name = path.name
            sample = {
                'pack_name': pack_name,
                'file_name': file_name,
                'name': f"{pack_name}/{file_name}",
                'full_path': file_path
            }
            samples.append(sample)
        
        # Build chain
        chain, name_to_index, slice_positions = chain_builder.build_chain(samples)
        
        # Check chain type
        self.assertIsInstance(chain, AudioSegment)
        
        # Check duration
        expected_duration = 500 * len(samples)
        self.assertEqual(len(chain), expected_duration)
        
        # Check mapping and slice positions
        self.assertEqual(len(name_to_index), len(samples))
        self.assertEqual(len(slice_positions), len(samples) + 1)
    
    def test_add_slice_points(self):
        """Test adding slice points to a WAV file."""
        chain_builder = M8ChainBuilder(500, 10)
        
        # Create a test chain
        files_to_use = self.test_files[:3]
        chain, name_to_index, slice_positions = chain_builder.build_chain_from_files(files_to_use)
        
        # Export to a WAV file
        output_path = os.path.join(self.temp_dir, "test_chain.wav")
        chain.export(output_path, format="wav")
        
        # Add slice points
        chain_builder.add_slice_points(output_path, slice_positions)
        
        # Extract slice points to verify
        slices = M8ChainExtractor.extract(output_path)
        
        # Should have the same number of slices
        self.assertEqual(len(slices), len(files_to_use))
        
        # Check first slice starts at 0
        self.assertEqual(slices[0][0], 0)
    
    def test_create_chain(self):
        """Test create_chain method."""
        chain_builder = M8ChainBuilder(500, 10)
        
        # Use a subset of test files
        files_to_use = self.test_files[:3]
        
        # Create output path
        output_path = os.path.join(self.temp_dir, "final_chain.wav")
        
        # Create chain
        result_path, name_to_index, slice_positions = chain_builder.create_chain(files_to_use, output_path)
        
        # Verify file exists
        self.assertTrue(os.path.exists(result_path))
        self.assertEqual(result_path, output_path)
        
        # Verify it contains slice points
        slices = M8ChainExtractor.extract(output_path)
        self.assertEqual(len(slices), len(files_to_use))
    
    def test_create_chain_with_nested_output_path(self):
        """Test create_chain with a nested output path."""
        chain_builder = M8ChainBuilder(500, 10)
        
        # Use a subset of test files
        files_to_use = self.test_files[:3]
        
        # Create a nested output path
        nested_dir = os.path.join(self.temp_dir, "nested", "output")
        output_path = os.path.join(nested_dir, "chain.wav")
        
        # Create chain
        result_path, _, _ = chain_builder.create_chain(files_to_use, output_path)
        
        # Verify directory was created and file exists
        self.assertTrue(os.path.exists(nested_dir))
        self.assertTrue(os.path.exists(result_path))
    
    def test_empty_input(self):
        """Test with empty input."""
        chain_builder = M8ChainBuilder(500, 10)
        
        # Empty file list
        with self.assertRaises(ValueError):
            chain_builder.create_chain([], os.path.join(self.temp_dir, "empty.wav"))
        
        # Empty samples list
        with self.assertRaises(ValueError):
            chain_builder.build_chain([])
    
    def test_too_many_samples(self):
        """Test with too many samples (M8 has a 255 sample limit)."""
        chain_builder = M8ChainBuilder(500, 10)
        
        # Create 256 sample dictionaries (exceeds M8 limit)
        samples = []
        for i in range(256):
            sample = {
                'pack_name': 'test',
                'file_name': f'sample_{i}.wav',
                'name': f'test/sample_{i}.wav',
                'full_path': self.test_files[0]  # Just use the same file for testing
            }
            samples.append(sample)
        
        # Should raise ValueError
        with self.assertRaises(ValueError):
            chain_builder.build_chain(samples)


if __name__ == '__main__':
    unittest.main()