#!/usr/bin/env python3
import os
import struct
import wave


class M8ChainExtractor:
    def __init__(self):
        pass
    
    def extract_slices(self, wav_file_path):
        """
        Extract slice data from M8 WAV files.
        
        Args:
            wav_file_path: Path to the WAV file
            
        Returns:
            List of tuples with (start, end) slice data
        
        Raises:
            ValueError: If the WAV file is invalid or contains no slices
        """
        # Read the entire file
        with open(wav_file_path, 'rb') as file:
            data = file.read()
            
        # Check if it's a valid RIFF/WAVE file
        if data[:4] != b'RIFF' or data[8:12] != b'WAVE':
            raise ValueError(f"Not a valid WAV file: {wav_file_path}")
            
        # Get the audio length
        with wave.open(wav_file_path, 'rb') as wav:
            length = wav.getnframes()
            
        # Find cue chunk
        cue_pos = data.find(b'cue ')
        if cue_pos < 0:
            raise ValueError(f"No cue chunk found in WAV file: {wav_file_path}")
            
        # Skip to number of cue points (4 bytes after 'cue ' and chunk size)
        num_cues_pos = cue_pos + 8
        num_cues = struct.unpack('<I', data[num_cues_pos:num_cues_pos+4])[0]
        
        if num_cues <= 0:
            raise ValueError(f"No cue points found in WAV file: {wav_file_path}")
            
        # Extract all cue points
        slice_points = []
        cue_data_pos = num_cues_pos + 4
        
        # Extract all sample offsets
        for i in range(num_cues):
            # Skip to the sample offset position (20 bytes from start of this cue point)
            sample_offset_pos = cue_data_pos + (i * 24) + 20
            
            # Read the sample offset
            sample_offset = struct.unpack('<I', data[sample_offset_pos:sample_offset_pos+4])[0]
            slice_points.append(sample_offset)
        
        # Create slices from slice points
        slices = []
        
        # Process only actual slices (skip the last point if it equals the file length)
        valid_slices = len(slice_points)
        if slice_points and slice_points[-1] == length:
            valid_slices -= 1
            
        for i in range(valid_slices):
            slice_start = slice_points[i]
            
            # Set the end point to either the next slice start or the file length
            if i < valid_slices - 1:
                slice_end = slice_points[i + 1]
            else:
                slice_end = length
                
            # Skip slices with zero length
            if slice_start == slice_end:
                continue
                
            slices.append((slice_start, slice_end))
        
        # Check if we found any valid slices
        if not slices:
            raise ValueError(f"No valid slices found in WAV file: {wav_file_path}")
            
        return slices
    
    def extract_slices_from_bytes(self, wav_data):
        """
        Extract slice data from WAV file data.
        
        Args:
            wav_data: Binary WAV file data
            
        Returns:
            List of tuples with (start, end) slice data
            
        Raises:
            ValueError: If the WAV data is invalid or contains no slices
        """
        # Create a temporary file to work with the data
        temp_file = None
        try:
            import tempfile
            
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp:
                temp_file = temp.name
                temp.write(wav_data)
            
            # Use the file-based extraction method
            return self.extract_slices(temp_file)
            
        finally:
            # Clean up the temporary file
            if temp_file and os.path.exists(temp_file):
                os.unlink(temp_file)
    
    @classmethod
    def extract(cls, wav_file_path_or_data):
        """
        Class method for one-step extraction of slice data.
        
        Args:
            wav_file_path_or_data: Path to WAV file or WAV file data
            
        Returns:
            List of tuples with (start, end) slice data
        """
        extractor = cls()
        
        if isinstance(wav_file_path_or_data, str):
            return extractor.extract_slices(wav_file_path_or_data)
        else:
            return extractor.extract_slices_from_bytes(wav_file_path_or_data)


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Extract slice data from M8-sliced WAV files')
    parser.add_argument('input_file', help='Input WAV file path')
    
    args = parser.parse_args()
    
    try:
        slices = M8ChainExtractor.extract(args.input_file)
        print(f"Found {len(slices)} slices in {args.input_file}:")
        for i, (start, end) in enumerate(slices):
            print(f"  Slice {i}: {start} to {end} ({end - start} samples)")
        return 0
    except Exception as e:
        print(f"Error: {e}")
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())