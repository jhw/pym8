#!/usr/bin/env python3
"""
WAV Chunk Lister - Lists all chunks in WAV files showing their names and sizes
"""

import os
import sys
import struct
import argparse
from pydub import AudioSegment

def list_wav_chunks(filename):
    """List all chunks in a WAV file with their names and sizes."""
    try:
        # Verify the file exists
        if not os.path.isfile(filename):
            print(f"Error: File '{filename}' not found")
            return
            
        # Open the file and read its data
        with open(filename, 'rb') as file:
            data = file.read()
            
        # Check if it's a valid RIFF/WAVE file
        if data[:4] != b'RIFF' or data[8:12] != b'WAVE':
            print(f"Error: '{filename}' is not a valid WAV file")
            return
            
        # Get total file size
        file_size = len(data)
        riff_size = struct.unpack('<I', data[4:8])[0] + 8  # RIFF size + 8 bytes for RIFF header
        
        print(f"\nWAV Chunks in '{filename}':")
        print(f"Total file size: {file_size} bytes")
        print(f"RIFF chunk size: {riff_size} bytes")
        print("\nChunk Structure:")
        print("-" * 50)
        print(f"{'Offset':<10} {'Chunk ID':<10} {'Size':<12} {'Description'}")
        print("-" * 50)
        
        # RIFF/WAVE header is special
        print(f"{0:<10} {'RIFF':<10} {riff_size:<12} {'RIFF container'}")
        print(f"{8:<10} {'WAVE':<10} {'N/A':<12} {'WAV format identifier'}")
        
        # Process all chunks after the RIFF/WAVE header
        pos = 12  # Start after RIFF header and WAVE identifier
        
        while pos + 8 <= file_size:  # Need at least 8 bytes for chunk header + size
            chunk_id = data[pos:pos+4]
            chunk_size_bytes = data[pos+4:pos+8]
            
            # Check for valid chunk ID (should be ASCII letters or spaces)
            if not all(c == 32 or (c >= 65 and c <= 122) for c in chunk_id):
                # This might not be a valid chunk, possibly we've gone past the end of data
                break
                
            chunk_id_str = chunk_id.decode('ascii', errors='replace')
            chunk_size = struct.unpack('<I', chunk_size_bytes)[0]
            
            # Determine chunk description
            description = get_chunk_description(chunk_id_str)
            
            # Print chunk info
            print(f"{pos:<10} {chunk_id_str:<10} {chunk_size:<12} {description}")
            
            # Move to next chunk (including padding byte if needed)
            pos += 8 + chunk_size
            if chunk_size % 2: 
                pos += 1  # Add padding byte if chunk size is odd
        
        print("-" * 50)
            
    except Exception as e:
        print(f"Error processing file: {str(e)}")

def get_chunk_description(chunk_id):
    """Return a description for common chunk types."""
    descriptions = {
        'fmt ': 'Audio format data',
        'data': 'Audio sample data',
        'fact': 'Fact chunk',
        'LIST': 'List container',
        'INFO': 'Information container',
        'JUNK': 'Padding chunk',
        'bext': 'Broadcast Extension',
        'iXML': 'iXML metadata',
        'id3 ': 'ID3 metadata',
        'smpl': 'Sample chunk',
        'inst': 'Instrument chunk',
        'cue ': 'Cue points',
        'plst': 'Playlist',
        'adtl': 'Associated data list',
        'slc1': 'M8 slice data (old)',
        'slc2': 'M8 slice data (new)'
    }
    
    return descriptions.get(chunk_id, 'Unknown chunk type')

def main():
    parser = argparse.ArgumentParser(description='List all chunks in WAV files')
    parser.add_argument('files', metavar='FILE', nargs='+', help='WAV file(s) to analyze')
    
    args = parser.parse_args()
    
    for filename in args.files:
        list_wav_chunks(filename)

if __name__ == "__main__":
    main()
