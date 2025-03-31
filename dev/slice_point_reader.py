#!/usr/bin/env python3
"""
M8 Slice Point Reader - Extracts slice points from Dirtywave M8 WAV files using standard cue points
"""

import os
import sys
import struct
import argparse

def extract_cue_points(data_bytes):
    """
    Extract cue point data from a standard WAV cue chunk.
    
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
    result = {}
    
    if len(data_bytes) < 4:
        return {"Error": "Cue chunk too small"}
    
    # Get number of cue points
    num_cues = struct.unpack('<I', data_bytes[0:4])[0]
    result["NumberOfSlices"] = num_cues
    
    # Check if the size is consistent with the number of cue points
    expected_size = 4 + (num_cues * 24)  # 4 bytes for count + 24 bytes per cue point
    if len(data_bytes) < expected_size:
        result["Warning"] = f"Cue chunk size ({len(data_bytes)}) smaller than expected ({expected_size})"
    
    # Extract each cue point
    cue_points = []
    slice_positions = []
    
    for i in range(num_cues):
        base_offset = 4 + (i * 24)
        
        # Check if we have enough data for this cue point
        if base_offset + 24 > len(data_bytes):
            break
            
        cue_id = struct.unpack('<I', data_bytes[base_offset:base_offset+4])[0]
        position = struct.unpack('<I', data_bytes[base_offset+4:base_offset+8])[0]
        data_chunk_id = data_bytes[base_offset+8:base_offset+12].decode('ascii', errors='replace')
        chunk_start = struct.unpack('<I', data_bytes[base_offset+12:base_offset+16])[0]
        block_start = struct.unpack('<I', data_bytes[base_offset+16:base_offset+20])[0]
        sample_offset = struct.unpack('<I', data_bytes[base_offset+20:base_offset+24])[0]
        
        cue_points.append({
            "ID": cue_id,
            "Position": position,
            "DataChunkID": data_chunk_id,
            "ChunkStart": chunk_start,
            "BlockStart": block_start,
            "SampleOffset": sample_offset
        })
        
        # Add to the simple slice positions list
        slice_positions.append(position)
    
    result["CuePoints"] = cue_points
    
    # For M8 users - extract just the positions for easier reference
    # The M8 appears to store the actual slice points in the SampleOffset field
    sample_offsets = [cue["SampleOffset"] for cue in cue_points]
    if sample_offsets:
        result["SlicePositions"] = sample_offsets
    
    return result

def get_m8_slice_points(filename):
    """Extract M8 slice points from a WAV file's cue chunk."""
    result = {"Filename": filename}
    
    try:
        # Verify the file exists
        if not os.path.isfile(filename):
            return {"Error": f"File '{filename}' not found"}
            
        # Open the file and read its data
        with open(filename, 'rb') as file:
            data = file.read()
            
        # Check if it's a valid RIFF/WAVE file
        if data[:4] != b'RIFF' or data[8:12] != b'WAVE':
            return {"Error": f"'{filename}' is not a valid WAV file"}
        
        # Look for the cue chunk
        cue_pos = data.find(b'cue ')
        
        if cue_pos >= 0:
            # Found a cue chunk
            chunk_size_bytes = data[cue_pos + 4:cue_pos + 8]
            chunk_size = struct.unpack('<I', chunk_size_bytes)[0]
            
            # Extract the chunk data
            chunk_data_start = cue_pos + 8
            chunk_data_end = chunk_data_start + chunk_size
            chunk_data = data[chunk_data_start:chunk_data_end]
            
            # Process the chunk data
            result["M8SliceData"] = {
                "ChunkType": "cue ",
                "ChunkSize": chunk_size,
                **extract_cue_points(chunk_data)
            }
            
            return result
        
        # If we get here, no cue data was found
        return {
            "Filename": filename,
            "M8SliceData": {"Status": "No cue points (slices) found in this WAV file"}
        }
        
    except Exception as e:
        return {"Error": f"Error processing file: {str(e)}"}

def print_metadata(metadata, indent=0):
    """Print metadata in a readable, indented format."""
    prefix = ' ' * indent
    
    for key, value in metadata.items():
        if value is None:
            print(f"{prefix}{key}: None")
        elif isinstance(value, dict):
            print(f"{prefix}{key}:")
            print_metadata(value, indent + 2)
        elif isinstance(value, (list, tuple)):
            print(f"{prefix}{key}:")
            for i, item in enumerate(value):
                if isinstance(item, dict):
                    print(f"{prefix}  Item {i}:")
                    print_metadata(item, indent + 4)
                elif item is None:
                    print(f"{prefix}  Item {i}: None")
                else:
                    print(f"{prefix}  Item {i}: {item}")
        else:
            print(f"{prefix}{key}: {value}")

def main():
    parser = argparse.ArgumentParser(description='Extract M8 slice points from WAV files using cue points')
    parser.add_argument('files', metavar='FILE', nargs='*', default=['dev/YAXU-DEMO-BREAK.wav'],
                        help='WAV file(s) to analyze (defaults to dev/SLICED4.wav if not specified)')
    
    args = parser.parse_args()
    
    for filename in args.files:
        print(f"\n=== M8 Slice Data for {filename} ===")
        metadata = get_m8_slice_points(filename)
        print_metadata(metadata)

if __name__ == "__main__":
    main()
