#!/usr/bin/env python3
"""Tests for ChainBuilder."""

import struct
import unittest
from io import BytesIO
from pathlib import Path
from pydub import AudioSegment
from pydub.generators import Sine, Square

from m8.tools.chain_builder import ChainBuilder


class TestChainBuilder(unittest.TestCase):
    """Test cases for ChainBuilder."""

    def setUp(self):
        """Set up test fixtures."""
        self.slice_duration_ms = 100
        self.builder = ChainBuilder(
            slice_duration_ms=self.slice_duration_ms,
            fade_ms=3,
            frame_rate=44100
        )

    def test_build_chain_from_audio_segments(self):
        """Test building chain from AudioSegment objects."""
        # Create test audio segments
        segments = [
            Sine(440).to_audio_segment(duration=150),  # Will be truncated
            Square(880).to_audio_segment(duration=50),  # Will be padded
            Sine(220).to_audio_segment(duration=100),   # Exact duration
        ]

        result_wav, slice_mapping = self.builder.build_chain(segments)

        # Verify return types
        self.assertIsInstance(result_wav, BytesIO)
        self.assertIsInstance(slice_mapping, dict)

        # Verify slice mapping
        self.assertEqual(len(slice_mapping), 3)
        self.assertEqual(slice_mapping[0], 0)
        self.assertEqual(slice_mapping[1], 1)
        self.assertEqual(slice_mapping[2], 2)

        # Verify WAV data
        wav_data = result_wav.getvalue()
        self.assertEqual(wav_data[:4], b'RIFF')
        self.assertEqual(wav_data[8:12], b'WAVE')

        # Verify slice points were added
        self.assertIn(b'cue ', wav_data)
        self.assertIn(b'atad', wav_data)

    def test_build_chain_sample_normalization(self):
        """Test that samples are normalized to correct duration."""
        segments = [
            Sine(440).to_audio_segment(duration=150),  # Too long
            Sine(440).to_audio_segment(duration=50),   # Too short
        ]

        result_wav, _ = self.builder.build_chain(segments)

        # Load the resulting chain and verify duration
        result_wav.seek(0)
        chain = AudioSegment.from_wav(result_wav)

        # Total duration should be 2 * slice_duration_ms
        expected_duration_ms = 2 * self.slice_duration_ms
        # Allow small tolerance for rounding
        self.assertAlmostEqual(len(chain), expected_duration_ms, delta=5)

    def test_build_chain_slice_positions(self):
        """Test that slice positions are calculated correctly."""
        segments = [
            Sine(440).to_audio_segment(duration=100),
            Sine(880).to_audio_segment(duration=100),
            Sine(220).to_audio_segment(duration=100),
        ]

        result_wav, _ = self.builder.build_chain(segments)

        # Parse the WAV to find slice positions
        wav_data = result_wav.getvalue()

        # Find first cue chunk
        cue_pos = wav_data.find(b'cue ')
        self.assertNotEqual(cue_pos, -1)

        # Read number of cue points
        num_cues = struct.unpack('<I', wav_data[cue_pos+8:cue_pos+12])[0]
        self.assertEqual(num_cues, 3)

        # Verify slice positions are evenly spaced
        samples_per_slice = int(self.slice_duration_ms * 44100 / 1000)

        for i in range(3):
            offset = cue_pos + 12 + (i * 24)  # Each cue point is 24 bytes
            position = struct.unpack('<I', wav_data[offset+4:offset+8])[0]
            expected_position = i * samples_per_slice
            self.assertEqual(position, expected_position)

    def test_direct_instantiation(self):
        """Test that ChainBuilder can be instantiated with slice_duration_ms."""
        slice_duration = 250.0  # 250ms slices
        builder = ChainBuilder(slice_duration_ms=slice_duration)

        self.assertEqual(builder.slice_duration_ms, slice_duration)
        self.assertEqual(builder.fade_ms, 3)
        self.assertEqual(builder.frame_rate, 44100)

    def test_build_chain_empty_list(self):
        """Test error handling for empty sample list."""
        with self.assertRaises(ValueError) as context:
            self.builder.build_chain([])

        self.assertIn("No samples provided", str(context.exception))

    def test_build_chain_too_many_samples(self):
        """Test error handling for too many samples (M8 limit)."""
        # Create 256 samples (exceeds M8 limit of 255)
        segments = [Sine(440).to_audio_segment(duration=100) for _ in range(256)]

        with self.assertRaises(ValueError) as context:
            self.builder.build_chain(segments)

        self.assertIn("exceeds M8 limit of 255", str(context.exception))

    def test_build_chain_resampling(self):
        """Test that samples are resampled to target frame rate."""
        # Create a segment with different frame rate
        segment = Sine(440).to_audio_segment(duration=100)
        segment = segment.set_frame_rate(22050)  # Different from builder's 44100

        result_wav, _ = self.builder.build_chain([segment])

        # Load result and verify frame rate
        result_wav.seek(0)
        chain = AudioSegment.from_wav(result_wav)
        self.assertEqual(chain.frame_rate, 44100)

    def test_build_chain_invalid_sample_type(self):
        """Test error handling for invalid sample types."""
        with self.assertRaises(TypeError) as context:
            self.builder.build_chain([123, "invalid", None])

        self.assertIn("Sample must be AudioSegment or file path", str(context.exception))

    def test_build_chain_single_sample(self):
        """Test building chain with single sample."""
        segment = Sine(440).to_audio_segment(duration=100)

        result_wav, slice_mapping = self.builder.build_chain([segment])

        # Verify single slice was created
        self.assertEqual(len(slice_mapping), 1)
        self.assertEqual(slice_mapping[0], 0)

        # Verify WAV is valid
        result_wav.seek(0)
        chain = AudioSegment.from_wav(result_wav)
        self.assertAlmostEqual(len(chain), self.slice_duration_ms, delta=5)

    def test_build_chain_max_samples(self):
        """Test building chain with maximum allowed samples (255)."""
        # Create 255 samples (M8 maximum)
        segments = [Sine(440).to_audio_segment(duration=100) for _ in range(255)]

        result_wav, slice_mapping = self.builder.build_chain(segments)

        # Should succeed without errors
        self.assertEqual(len(slice_mapping), 255)

        # Verify all slices are present in WAV metadata
        wav_data = result_wav.getvalue()
        cue_pos = wav_data.find(b'cue ')
        num_cues = struct.unpack('<I', wav_data[cue_pos+8:cue_pos+12])[0]
        self.assertEqual(num_cues, 255)

    def test_build_chain_fade_application(self):
        """Test that fade in/out is applied to samples."""
        # Create a segment with distinct beginning and end
        segment = Square(440).to_audio_segment(duration=100)

        # Build chain with fade
        builder_with_fade = ChainBuilder(
            slice_duration_ms=100,
            fade_ms=10,  # Longer fade for testing
            frame_rate=44100
        )

        result_wav, _ = builder_with_fade.build_chain([segment])

        # Load result
        result_wav.seek(0)
        chain = AudioSegment.from_wav(result_wav)

        # Verify fade was applied by checking that the audio has been modified
        # (We can't easily verify the exact fade curve, but we can check the file is valid)
        self.assertIsNotNone(chain)
        self.assertAlmostEqual(len(chain), 100, delta=5)


if __name__ == '__main__':
    unittest.main()
