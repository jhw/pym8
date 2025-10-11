#!/usr/bin/env python3
import os
import struct
import wave


class M8ChainSlicer:
    """Tool for creating evenly spaced slice points in WAV files for Dirtywave M8."""

    def __init__(self, num_slices=4):
        """Initialize with configuration options.

        Args:
            num_slices: Number of slices to create (default: 4)
        """
        self.num_slices = num_slices
    
    def create_slice_points(self, length):
        """Create evenly spaced slice points.
        
        Args:
            length: Length of the WAV file in frames/samples
            
        Returns:
            List of slice point positions
        """
        if self.num_slices <= 0:
            return []
        
        # Calculate the interval between slices
        interval = length // self.num_slices
        
        # Create the slice points
        slice_points = [i * interval for i in range(self.num_slices)]
        
        return slice_points
    
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
            slice_points: List of slice point positions
            
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
            slice_points: List of slice point positions
            
        Returns:
            Bytes containing the complete M8-specific cue chunk
        """
        # Chunk header
        chunk_id = b'cue '
        
        # Number of cue points
        num_cues = len(slice_points)
        cue_data = struct.pack('<I', num_cues)
        
        # Add each cue point with the special M8 format
        for i, position in enumerate(slice_points):
            cue_id = i  # IDs start from 0 in the M8 format
            position_value = 0  # Position is always 0 in M8 format
            data_chunk_id = b'atad'  # Reversed 'data'
            chunk_start = 0
            block_start = 0
            sample_offset = position
            
            cue_data += struct.pack('<I', cue_id)
            cue_data += struct.pack('<I', position_value)
            cue_data += data_chunk_id
            cue_data += struct.pack('<I', chunk_start)
            cue_data += struct.pack('<I', block_start)
            cue_data += struct.pack('<I', sample_offset)
        
        # Calculate chunk size
        chunk_size = len(cue_data)
        
        # Return full chunk with header
        return chunk_id + struct.pack('<I', chunk_size) + cue_data
    
    def process_wav_file(self, input_file, output_file=None):
        """Add slice points to a WAV file in M8 format.
        
        Args:
            input_file: Path to input WAV file
            output_file: Path to output WAV file (if None, generates name based on input)
            
        Returns:
            Path to output file if successful, None otherwise
        """
        # Verify the file exists and is a WAV
        if not os.path.isfile(input_file):
            raise FileNotFoundError(f"File '{input_file}' not found")
        
        # Generate output filename if not provided
        if output_file is None:
            base_name, ext = os.path.splitext(input_file)
            output_file = f"{base_name}-{self.num_slices}slices{ext}"
        
        try:
            # Read the file
            with open(input_file, 'rb') as file:
                data = file.read()
                
            # Check if it's a valid RIFF/WAVE file
            if data[:4] != b'RIFF' or data[8:12] != b'WAVE':
                raise ValueError(f"'{input_file}' is not a valid WAV file")
            
            # Get the audio length
            with wave.open(input_file, 'rb') as wav:
                length = wav.getnframes()
            
            # Create slice points
            slice_points = self.create_slice_points(length)
            if not slice_points:
                raise ValueError("No slice points created. Check number of slices.")
            
            # Create standard cue chunk
            standard_cue_chunk = self.create_standard_cue_chunk(slice_points)
            
            # Find the fmt chunk to insert standard cue chunk after it
            fmt_pos = data.find(b'fmt ')
            if fmt_pos < 0:
                raise ValueError("Could not find 'fmt ' chunk in WAV file")
            
            # Get the size of the fmt chunk
            fmt_chunk_size = struct.unpack('<I', data[fmt_pos+4:fmt_pos+8])[0]
            # Calculate end of fmt chunk (including padding byte if needed)
            fmt_end = fmt_pos + 8 + fmt_chunk_size
            if fmt_chunk_size % 2:
                fmt_end += 1
            
            # Insert standard cue chunk after fmt chunk, before data chunk
            data_pos = data.find(b'data')
            if data_pos < 0:
                raise ValueError("Could not find 'data' chunk in WAV file")
            
            # Insert standard cue chunk
            new_data = data[:fmt_end] + standard_cue_chunk + data[fmt_end:]
            
            # Create M8-specific 'atad' cue chunk
            m8_cue_chunk = self.create_m8_atad_cue_chunk(slice_points)
            
            # Add M8-specific cue chunk at the end, after data chunk
            new_data = new_data + m8_cue_chunk
            
            # Update the RIFF size
            riff_size = len(new_data) - 8  # Total size minus RIFF header
            new_data = new_data[:4] + struct.pack('<I', riff_size) + new_data[8:]
            
            # Write the new file
            with open(output_file, 'wb') as file:
                file.write(new_data)
                
            return output_file
                
        except Exception as e:
            raise RuntimeError(f"Error processing file: {str(e)}")
    
    @classmethod
    def slice_file(cls, input_file, num_slices=4, output_file=None):
        """Class method for one-step slicing of WAV files.
        
        Args:
            input_file: Path to input WAV file
            num_slices: Number of slices to create
            output_file: Path to output file (if None, generates name based on input)
            
        Returns:
            Path to output file if successful, None otherwise
        """
        slicer = cls(num_slices)
        return slicer.process_wav_file(input_file, output_file)


def main():
    """CLI entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Add evenly spaced slice points to WAV files for Dirtywave M8')
    parser.add_argument('input_file', help='Input WAV file path')
    parser.add_argument('--slices', '-s', type=int, default=4, help='Number of slices to create (default: 4)')
    parser.add_argument('--output', '-o', help='Output file path (optional)')
    
    args = parser.parse_args()
    
    try:
        output_file = M8ChainSlicer.slice_file(args.input_file, args.slices, args.output)
        print(f"Successfully wrote sliced WAV to {output_file}")
        return 0
    except Exception as e:
        print(f"Error: {e}")
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())