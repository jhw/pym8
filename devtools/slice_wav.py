#!/usr/bin/env python3
"""
M8 WAV Slicer v2 - Creates evenly spaced slice points in WAV files for Dirtywave M8
with both standard cue points and M8-specific 'atad' cue points
"""

import os
import struct
import argparse
import wave

def create_slice_points(length, num_slices):
    """Create evenly spaced slice points."""
    if num_slices <= 0:
        return []
    
    # Calculate the interval between slices
    interval = length // num_slices
    
    # Create the slice points
    slice_points = [i * interval for i in range(num_slices)]
    
    return slice_points

def create_standard_cue_chunk(slice_points):
    """
    Create a standard WAV cue chunk with the specified slice points.
    Standard cue chunk format:
    - 4 bytes: Number of cue points (uint32)
    - For each cue point:
      - 4 bytes: Cue ID (uint32)
      - 4 bytes: Position (uint32) - sample offset
      - 4 bytes: Data chunk ID (4 chars, usually 'data')
      - 4 bytes: Chunk start (uint32)
      - 4 bytes: Block start (uint32)
      - 4 bytes: Sample offset (uint32)
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

def create_m8_atad_cue_chunk(slice_points):
    """
    Create M8-specific cue chunk with 'atad' chunk ID.
    Based on the structure observed in M8SLICED.wav
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

def add_slice_points_to_wav_m8_format(input_file, output_file, num_slices, length):
    """Add slice points to a WAV file in M8 format with both standard and M8-specific cue chunks."""
    # Verify the file exists and is a WAV
    if not os.path.isfile(input_file):
        print(f"Error: File '{input_file}' not found")
        return False
    
    try:
        # Read the file
        with open(input_file, 'rb') as file:
            data = file.read()
            
        # Check if it's a valid RIFF/WAVE file
        if data[:4] != b'RIFF' or data[8:12] != b'WAVE':
            print(f"Error: '{input_file}' is not a valid WAV file")
            return False
        
        # Get the actual audio length if not specified
        if length <= 0:
            with wave.open(input_file, 'rb') as wav:
                length = wav.getnframes()
                print(f"Using WAV file length: {length} frames")
        
        # Create slice points
        slice_points = create_slice_points(length, num_slices)
        if not slice_points:
            print("Error: No slice points created. Check number of slices.")
            return False
        
        print(f"Created {len(slice_points)} slice points: {slice_points}")
        
        # Create standard cue chunk
        standard_cue_chunk = create_standard_cue_chunk(slice_points)
        
        # Find the fmt chunk to insert standard cue chunk after it
        fmt_pos = data.find(b'fmt ')
        if fmt_pos < 0:
            print("Error: Could not find 'fmt ' chunk in WAV file")
            return False
        
        # Get the size of the fmt chunk
        fmt_chunk_size = struct.unpack('<I', data[fmt_pos+4:fmt_pos+8])[0]
        # Calculate end of fmt chunk (including padding byte if needed)
        fmt_end = fmt_pos + 8 + fmt_chunk_size
        if fmt_chunk_size % 2:
            fmt_end += 1
        
        # Insert standard cue chunk after fmt chunk, before data chunk
        data_pos = data.find(b'data')
        if data_pos < 0:
            print("Error: Could not find 'data' chunk in WAV file")
            return False
        
        # Insert standard cue chunk
        print("Adding standard cue chunk after fmt chunk")
        new_data = data[:fmt_end] + standard_cue_chunk + data[fmt_end:]
        
        # Create M8-specific 'atad' cue chunk
        m8_cue_chunk = create_m8_atad_cue_chunk(slice_points)
        
        # Add M8-specific cue chunk at the end, after data chunk
        print("Adding M8-specific 'atad' cue chunk at the end")
        new_data = new_data + m8_cue_chunk
        
        # Update the RIFF size
        riff_size = len(new_data) - 8  # Total size minus RIFF header
        new_data = new_data[:4] + struct.pack('<I', riff_size) + new_data[8:]
        
        # Write the new file
        with open(output_file, 'wb') as file:
            file.write(new_data)
            
        print(f"Successfully wrote sliced WAV to {output_file} with both standard and M8-specific cue chunks")
        return True
        
    except Exception as e:
        print(f"Error processing file: {str(e)}")
        return False

def main():
    parser = argparse.ArgumentParser(description='Add evenly spaced slice points to WAV files for Dirtywave M8')
    parser.add_argument('input_file', help='Input WAV file path')
    parser.add_argument('--slices', '-s', type=int, default=4, help='Number of slices to create (default: 4)')
    
    args = parser.parse_args()
    
    # Generate output filename with number of slices in the same directory as input
    input_path = args.input_file
    base_name, ext = os.path.splitext(input_path)
    output_file = f"{base_name}-{args.slices}{ext}"
    
    # Process the file
    add_slice_points_to_wav_m8_format(input_path, output_file, args.slices, 0)

if __name__ == "__main__":
    main()