#!/usr/bin/env python3
"""Chain Builder - Tool for creating M8 sample chains with slice metadata."""

from io import BytesIO
from pathlib import Path
from pydub import AudioSegment
from m8.tools.wav_slicer import WAVSlicer


class ChainBuilder:
    """Build sample chains with slice metadata for M8 tracker."""

    def __init__(self, sample_duration_ms, fade_ms=3, frame_rate=44100):
        """Initialize chain builder.

        Args:
            sample_duration_ms: Duration of each sample slice in milliseconds
            fade_ms: Fade in/out duration in milliseconds (default: 3)
            frame_rate: Sample rate in Hz (default: 44100)
        """
        self.sample_duration_ms = sample_duration_ms
        self.fade_ms = fade_ms
        self.frame_rate = frame_rate
        self.wav_slicer = WAVSlicer()

    def build_chain(self, samples):
        """Build a sample chain from a list of audio samples.

        Args:
            samples: List of AudioSegment objects or file paths (Path/str)

        Returns:
            tuple: (BytesIO containing WAV with slice metadata, slice_index_mapping)
                  slice_index_mapping is dict mapping original index to slice index
        """
        if not samples:
            raise ValueError("No samples provided")

        if len(samples) > 255:
            raise ValueError(f"Chain has {len(samples)} samples, exceeds M8 limit of 255")

        # Load and process all samples
        processed_segments = []
        slice_index_mapping = {}

        for idx, sample in enumerate(samples):
            # Load sample if it's a file path
            if isinstance(sample, (str, Path)):
                segment = AudioSegment.from_file(str(sample))
            elif isinstance(sample, AudioSegment):
                segment = sample
            else:
                raise TypeError(f"Sample must be AudioSegment or file path, got {type(sample)}")

            # Resample to target frame rate if needed
            if segment.frame_rate != self.frame_rate:
                segment = segment.set_frame_rate(self.frame_rate)

            # Normalize to sample duration (truncate or pad)
            if len(segment) > self.sample_duration_ms:
                segment = segment[:int(self.sample_duration_ms)]
            elif len(segment) < self.sample_duration_ms:
                silence_duration = int(self.sample_duration_ms - len(segment))
                silence = AudioSegment.silent(
                    duration=silence_duration,
                    frame_rate=self.frame_rate
                )
                segment = segment + silence

            # Apply fade in/out to avoid clicks at slice boundaries
            fade_duration = min(self.fade_ms, len(segment) // 10)
            if fade_duration > 0:
                segment = segment.fade_in(int(fade_duration))
                segment = segment.fade_out(int(fade_duration))

            processed_segments.append(segment)
            slice_index_mapping[idx] = idx

        # Calculate slice positions (in samples, not milliseconds)
        samples_per_segment = int(self.sample_duration_ms * self.frame_rate / 1000)
        slice_positions = [i * samples_per_segment for i in range(len(processed_segments))]

        # Concatenate all segments into a single chain
        chain = processed_segments[0]
        for segment in processed_segments[1:]:
            chain = chain + segment

        # Export chain to WAV format in memory
        wav_buffer = BytesIO()
        chain.export(wav_buffer, format="wav")
        wav_data = wav_buffer.getvalue()

        # Add slice point metadata using WAVSlicer
        sliced_wav = self.wav_slicer.add_slice_points(wav_data, slice_positions)

        return sliced_wav, slice_index_mapping

    @classmethod
    def from_bpm(cls, bpm, ticks_per_beat=16, fade_ms=3, frame_rate=44100):
        """Create a ChainBuilder with sample duration based on BPM and ticks.

        Args:
            bpm: Beats per minute
            ticks_per_beat: Number of ticks per beat (default: 16)
            fade_ms: Fade in/out duration in milliseconds (default: 3)
            frame_rate: Sample rate in Hz (default: 44100)

        Returns:
            ChainBuilder instance configured for the given BPM
        """
        # Calculate duration of one tick in milliseconds
        beat_duration_ms = (60.0 / bpm) * 1000
        tick_duration_ms = beat_duration_ms / ticks_per_beat

        return cls(
            sample_duration_ms=tick_duration_ms,
            fade_ms=fade_ms,
            frame_rate=frame_rate
        )
