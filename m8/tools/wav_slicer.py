#!/usr/bin/env python3
"""WAV Slicer - Tool for adding slice point metadata to WAV files for M8 tracker."""

import struct
from io import BytesIO


class WAVSlicer:
    """Tool for adding slice points to WAV files for Dirtywave M8."""

    def create_standard_cue_chunk(self, slice_points):
        """Create a standard WAV cue chunk with the specified slice points.

        Standard cue chunk format:
        - 4 bytes: Number of cue points (uint32)
        - For each cue point:
          - 4 bytes: Cue ID (uint32)
          - 4 bytes: Position (uint32) - sample offset
          - 4 bytes: Data chunk ID (4 chars, usually 'data')
          - 4 bytes: Chunk start (uint32)
          - 4 bytes: Block start (uint32)
          - 4 bytes: Sample offset (uint32)

        Args:
            slice_points: List of slice point positions (in samples)

        Returns:
            Bytes containing the complete cue chunk
        """
        # Chunk header
        chunk_id = b'cue '

        # Number of cue points
        num_cues = len(slice_points)
        cue_data = struct.pack('<I', num_cues)

        # Add each cue point
        for i, position in enumerate(slice_points):
            cue_id = i + 1  # Start IDs from 1
            data_chunk_id = b'data'
            chunk_start = 0
            block_start = 0
            sample_offset = position

            cue_data += struct.pack('<I', cue_id)
            cue_data += struct.pack('<I', position)
            cue_data += data_chunk_id
            cue_data += struct.pack('<I', chunk_start)
            cue_data += struct.pack('<I', block_start)
            cue_data += struct.pack('<I', sample_offset)

        # Calculate chunk size
        chunk_size = len(cue_data)

        # Return full chunk with header
        return chunk_id + struct.pack('<I', chunk_size) + cue_data

    def create_m8_atad_cue_chunk(self, slice_points):
        """Create M8-specific cue chunk with 'atad' chunk ID.

        Based on the structure observed in M8 sliced WAV files.

        Args:
            slice_points: List of slice point positions (in samples)

        Returns:
            Bytes containing the complete M8-specific cue chunk
        """
        # Chunk header
        chunk_id = b'cue '

        # Number of cue points
        num_cues = len(slice_points)
        cue_data = struct.pack('<I', num_cues)

        # Add each cue point (M8-specific format uses 'atad' instead of 'data')
        for i, position in enumerate(slice_points):
            cue_id = i + 1
            data_chunk_id = b'atad'  # M8-specific
            chunk_start = 0
            block_start = 0
            sample_offset = position

            cue_data += struct.pack('<I', cue_id)
            cue_data += struct.pack('<I', position)
            cue_data += data_chunk_id
            cue_data += struct.pack('<I', chunk_start)
            cue_data += struct.pack('<I', block_start)
            cue_data += struct.pack('<I', sample_offset)

        # Calculate chunk size
        chunk_size = len(cue_data)

        # Return full chunk with header
        return chunk_id + struct.pack('<I', chunk_size) + cue_data

    def add_slice_points(self, wav_data, slice_points):
        """Add slice point metadata to WAV file data.

        Args:
            wav_data: Bytes object containing WAV file data
            slice_points: List of slice point positions (in samples)

        Returns:
            BytesIO object containing the WAV file with slice metadata
        """
        if not slice_points:
            # No slice points to add, return original data
            return BytesIO(wav_data)

        # Create standard cue chunk
        standard_cue_chunk = self.create_standard_cue_chunk(slice_points)

        # Find proper position to insert standard cue chunk (after fmt chunk)
        fmt_pos = wav_data.find(b'fmt ')
        if fmt_pos < 0:
            raise ValueError("Could not find 'fmt ' chunk in WAV file")

        # Get the size of the fmt chunk and calculate end position
        fmt_chunk_size = struct.unpack('<I', wav_data[fmt_pos+4:fmt_pos+8])[0]
        fmt_end = fmt_pos + 8 + fmt_chunk_size
        # Handle padding byte for odd-sized chunks
        if fmt_chunk_size % 2:
            fmt_end += 1

        # Insert standard cue chunk after fmt chunk
        new_data = wav_data[:fmt_end] + standard_cue_chunk + wav_data[fmt_end:]

        # Create M8-specific atad cue chunk
        m8_cue_chunk = self.create_m8_atad_cue_chunk(slice_points)

        # Add M8-specific cue chunk at the end
        new_data = new_data + m8_cue_chunk

        # Update the RIFF size
        riff_size = len(new_data) - 8  # Total size minus RIFF header
        new_data = new_data[:4] + struct.pack('<I', riff_size) + new_data[8:]

        return BytesIO(new_data)
