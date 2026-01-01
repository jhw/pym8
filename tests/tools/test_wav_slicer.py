#!/usr/bin/env python3
"""Tests for WAVSlicer."""

import struct
import unittest
from io import BytesIO
from pydub import AudioSegment
from pydub.generators import Sine

from m8.tools.wav_slicer import WAVSlicer


class TestWAVSlicer(unittest.TestCase):
    """Test cases for WAVSlicer."""

    def setUp(self):
        """Set up test fixtures."""
        self.slicer = WAVSlicer()

    def test_create_standard_cue_chunk(self):
        """Test creating standard cue chunk."""
        slice_points = [0, 1000, 2000, 3000]
        chunk = self.slicer.create_standard_cue_chunk(slice_points)

        # Check chunk header
        self.assertEqual(chunk[:4], b'cue ')

        # Check chunk size (4 bytes)
        chunk_size = struct.unpack('<I', chunk[4:8])[0]
        expected_size = 4 + (len(slice_points) * 24)  # 4 for count + 24 bytes per cue point
        self.assertEqual(chunk_size, expected_size)

        # Check number of cue points
        num_cues = struct.unpack('<I', chunk[8:12])[0]
        self.assertEqual(num_cues, len(slice_points))

        # Verify first cue point
        offset = 12
        cue_id = struct.unpack('<I', chunk[offset:offset+4])[0]
        position = struct.unpack('<I', chunk[offset+4:offset+8])[0]
        data_chunk_id = chunk[offset+8:offset+12]

        self.assertEqual(cue_id, 1)  # First cue ID should be 1
        self.assertEqual(position, slice_points[0])
        self.assertEqual(data_chunk_id, b'data')

    def test_create_m8_atad_cue_chunk(self):
        """Test creating M8-specific atad cue chunk."""
        slice_points = [0, 2000, 4000]
        chunk = self.slicer.create_m8_atad_cue_chunk(slice_points)

        # Check chunk header
        self.assertEqual(chunk[:4], b'cue ')

        # Check number of cue points
        num_cues = struct.unpack('<I', chunk[8:12])[0]
        self.assertEqual(num_cues, len(slice_points))

        # Verify M8-specific 'atad' marker in first cue point
        offset = 12
        data_chunk_id = chunk[offset+8:offset+12]
        self.assertEqual(data_chunk_id, b'atad')

    def test_add_slice_points_to_wav(self):
        """Test adding slice points to WAV file data."""
        # Create a simple WAV file using pydub
        tone = Sine(440).to_audio_segment(duration=1000)
        wav_buffer = BytesIO()
        tone.export(wav_buffer, format="wav")
        original_wav_data = wav_buffer.getvalue()

        # Add slice points
        slice_points = [0, 11025, 22050]  # Assuming 44100 Hz sample rate
        result = self.slicer.add_slice_points(original_wav_data, slice_points)

        # Verify result is BytesIO
        self.assertIsInstance(result, BytesIO)

        # Get the modified WAV data
        modified_wav_data = result.getvalue()

        # Check that modified file is larger (due to added cue chunks)
        self.assertGreater(len(modified_wav_data), len(original_wav_data))

        # Verify RIFF header is still valid
        self.assertEqual(modified_wav_data[:4], b'RIFF')
        self.assertEqual(modified_wav_data[8:12], b'WAVE')

        # Verify standard cue chunk exists
        self.assertIn(b'cue ', modified_wav_data)

        # Verify both cue chunks exist (one with 'data', one with 'atad')
        self.assertIn(b'data', modified_wav_data)
        self.assertIn(b'atad', modified_wav_data)

        # Verify RIFF size is updated correctly
        riff_size = struct.unpack('<I', modified_wav_data[4:8])[0]
        self.assertEqual(riff_size, len(modified_wav_data) - 8)

    def test_add_slice_points_empty_list(self):
        """Test adding empty slice points list returns original data."""
        # Create a simple WAV file
        tone = Sine(440).to_audio_segment(duration=500)
        wav_buffer = BytesIO()
        tone.export(wav_buffer, format="wav")
        original_wav_data = wav_buffer.getvalue()

        # Add no slice points
        result = self.slicer.add_slice_points(original_wav_data, [])

        # Should return original data unchanged
        self.assertEqual(result.getvalue(), original_wav_data)

    def test_add_slice_points_invalid_wav(self):
        """Test error handling for invalid WAV data."""
        invalid_data = b'NOT A WAV FILE'

        with self.assertRaises(ValueError) as context:
            self.slicer.add_slice_points(invalid_data, [0, 1000])

        self.assertIn("Could not find 'fmt ' chunk", str(context.exception))

    def test_single_slice_point(self):
        """Test handling of single slice point."""
        tone = Sine(440).to_audio_segment(duration=500)
        wav_buffer = BytesIO()
        tone.export(wav_buffer, format="wav")
        original_wav_data = wav_buffer.getvalue()

        slice_points = [0]
        result = self.slicer.add_slice_points(original_wav_data, slice_points)

        # Should successfully add slice metadata
        modified_wav_data = result.getvalue()
        self.assertGreater(len(modified_wav_data), len(original_wav_data))

        # Check number of cue points in standard cue chunk
        cue_pos = modified_wav_data.find(b'cue ')
        self.assertNotEqual(cue_pos, -1)
        num_cues = struct.unpack('<I', modified_wav_data[cue_pos+8:cue_pos+12])[0]
        self.assertEqual(num_cues, 1)


if __name__ == '__main__':
    unittest.main()
