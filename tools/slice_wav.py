#!/usr/bin/env python3
"""
M8 WAV Slicer - Creates evenly spaced slice points in WAV files for Dirtywave M8
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

def create_cue_chunk(slice_points):
    """
    Create a WAV cue chunk with the specified slice points.
    
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

def add_slice_points_to_wav(input_file, output_file, num_slices, length):
    """Add slice points to a WAV file."""
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
        
        # Create new cue chunk
        cue_chunk = create_cue_chunk(slice_points)
        
        # Find if there's an existing cue chunk to replace
        cue_pos = data.find(b'cue ')
        
        if cue_pos >= 0:
            # Replace existing cue chunk
            print("Replacing existing cue chunk")
            
            # Get the size of the existing chunk
            chunk_size = struct.unpack('<I', data[cue_pos+4:cue_pos+8])[0]
            
            # Calculate next chunk position (including padding byte if needed)
            next_pos = cue_pos + 8 + chunk_size
            if chunk_size % 2:
                next_pos += 1
            
            # Construct new file data with replaced cue chunk
            new_data = data[:cue_pos] + cue_chunk + data[next_pos:]
        else:
            # Insert new cue chunk before data chunk
            print("Adding new cue chunk")
            data_pos = data.find(b'data')
            
            if data_pos < 0:
                print("Error: Could not find 'data' chunk in WAV file")
                return False
            
            # Insert cue chunk before data chunk
            new_data = data[:data_pos] + cue_chunk + data[data_pos:]
        
        # Update the RIFF size
        riff_size = len(new_data) - 8  # Total size minus RIFF header
        new_data = new_data[:4] + struct.pack('<I', riff_size) + new_data[8:]
        
        # Write the new file
        with open(output_file, 'wb') as file:
            file.write(new_data)
            
        print(f"Successfully wrote sliced WAV to {output_file}")
        return True
        
    except Exception as e:
        print(f"Error processing file: {str(e)}")
        return False

def main():
    parser = argparse.ArgumentParser(description='Add evenly spaced slice points to WAV files for Dirtywave M8')
    parser.add_argument('input_file', help='Input WAV file path')
    parser.add_argument('--slices', '-s', type=int, required=True, help='Number of slices to create')
    parser.add_argument('--length', '-l', type=int, default=0, 
                        help='Length in samples to use for slice calculations (defaults to WAV length)')
    parser.add_argument('--output', '-o', help='Output file path (defaults to tmp/<input_filename>)')
    
    args = parser.parse_args()
    
    # Create tmp directory if it doesn't exist
    os.makedirs('tmp', exist_ok=True)
    
    # Set default output file if not specified
    if not args.output:
        filename = os.path.basename(args.input_file)
        args.output = os.path.join('tmp', filename)
    
    # Process the file
    add_slice_points_to_wav(args.input_file, args.output, args.slices, args.length)

if __name__ == "__main__":
    main()