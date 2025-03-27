#!/usr/bin/env python
"""
Script to inspect DW01 Synthdrums m8i files for sample paths.
Iterates through all m8i files in the directory and checks if they contain sample paths.
"""

import os
import sys
import struct
from pathlib import Path

# Sample path starts at offset 0x5B for these instruments
SAMPLE_PATH_OFFSET = 0x5B  # Offset of "S" in "Samples/" in the CLAP example
SAMPLE_PATH_LENGTH = 48   # Length for the path (restricted to reasonable length)

def hexdump(data, offset, length=64):
    """Generate a hexdump of the data starting at offset"""
    result = []
    for i in range(offset, min(offset + length, len(data)), 16):
        # Hex offset
        line = f"{i:08X}  "
        
        # Hex bytes
        hex_part = ""
        for j in range(i, min(i + 16, len(data))):
            hex_part += f"{data[j]:02X} "
        hex_part = hex_part.ljust(49)  # Padding for alignment
        line += hex_part
        
        # ASCII representation
        ascii_part = "|"
        for j in range(i, min(i + 16, len(data))):
            if 32 <= data[j] <= 126:  # Printable ASCII
                ascii_part += chr(data[j])
            else:
                ascii_part += "."
        ascii_part += "|"
        
        line += ascii_part
        result.append(line)
    
    return "\n".join(result)

def read_instrument_file(file_path):
    """Read an M8 instrument file and extract key information"""
    with open(file_path, 'rb') as f:
        data = f.read()
    
    if len(data) < 16:
        return None
    
    # Read instrument type ID
    instrument_type_id = data[0]
    
    # For these m8i files, the actual name appears to be in the filename
    # Extract it from the file name instead of trying to parse it from the file content
    instrument_name = Path(file_path).stem
    
    # First 8 bytes might be a version identifier ("8VERSION")
    version_str = ""
    for i in range(1, 9):
        if i >= len(data) or data[i] == 0:
            break
        if 32 <= data[i] <= 126:  # Printable ASCII
            version_str += chr(data[i])
    
    # Find any sample path in the file
    sample_path = ""
    sample_path_offset = -1
    
    # Look for the string "Samples" anywhere in the file
    for i in range(len(data) - 7):
        if data[i:i+7] == b'Samples':
            sample_path_offset = i
            break
            
    # If we found a sample path, extract it
    if sample_path_offset >= 0:
        # Extract the full path up to a null terminator or max length
        for i in range(sample_path_offset, min(sample_path_offset + SAMPLE_PATH_LENGTH, len(data))):
            if i >= len(data) or data[i] == 0:
                break
            # Only include printable ASCII characters
            if 32 <= data[i] <= 126:
                sample_path += chr(data[i])
    
    return {
        'type_id': instrument_type_id,
        'name': instrument_name,
        'version': version_str,
        'sample_path': sample_path,
        'sample_path_offset': sample_path_offset,
        'file_size': len(data),
        'has_sample_path': bool(sample_path)
    }

def main():
    """Main function to inspect DW01 Synthdrums directory"""
    if len(sys.argv) < 2:
        print("Usage: python inspect_dwsynthdrum_samples.py <DW01_Synthdrums_directory> [--detailed]")
        return 1
    
    base_dir = Path(sys.argv[1])
    detailed = "--detailed" in sys.argv
    
    if not base_dir.exists():
        print(f"Error: Directory {base_dir} does not exist")
        return 1
    
    print("\nInspecting DW01 Synthdrums instruments for sample paths\n")
    print(f"{'File Name':<20} {'Instrument Name':<15} {'Type ID':<10} {'Version':<10} {'Size':<8} {'Offset':<8} {'Sample Path':<50}")
    print("-" * 123)
    
    # Find all m8i files in the directory
    m8i_files = list(base_dir.glob("**/*.m8i"))
    
    if not m8i_files:
        print(f"No .m8i files found in {base_dir}")
        return 0
    
    # Process each file
    sample_count = 0
    instruments_with_samples = []
    
    for m8i_file in sorted(m8i_files):
        with open(m8i_file, 'rb') as f:
            data = f.read()
            
        info = read_instrument_file(m8i_file)
        if not info:
            print(f"Error reading {m8i_file.name}")
            continue
        
        # Format type ID as hex
        type_id_hex = f"0x{info['type_id']:02X} ({info['type_id']})"
        
        # Print the information
        sample_path = info['sample_path']
        if sample_path:
            sample_count += 1
            instruments_with_samples.append((m8i_file, info, data))
            
        # Truncate long paths and add ellipsis
        if len(sample_path) > 60:
            sample_path = sample_path[:57] + "..."
            
        offset_str = f"0x{info['sample_path_offset']:02X}" if info['sample_path_offset'] >= 0 else ""
        print(f"{m8i_file.name:<20} {info['name']:<15} {type_id_hex:<10} {info['version']:<10} {info['file_size']:<8} {offset_str:<8} {sample_path}")
    
    # Print detailed analysis if requested
    if detailed and instruments_with_samples:
        print("\n" + "=" * 80)
        print("DETAILED ANALYSIS OF INSTRUMENTS WITH SAMPLE PATHS")
        print("=" * 80)
        
        for m8i_file, info, data in instruments_with_samples:
            print(f"\nFile: {m8i_file.name}")
            print(f"Instrument Name: {info['name']}")
            print(f"Type ID: 0x{info['type_id']:02X} ({info['type_id']})")
            print(f"Version: {info['version']}")
            print(f"Sample Path: {info['sample_path']}")
            print(f"Sample Path Offset: 0x{info['sample_path_offset']:02X}")
            
            # Calculate context before and after sample path
            context_start = max(0, info['sample_path_offset'] - 32)
            print(f"\nHex dump from offset 0x{context_start:02X}:")
            print(hexdump(data, context_start, 128))
            print("")
    
    # Print summary
    print("\nSummary:")
    print(f"Total instruments: {len(m8i_files)}")
    print(f"Instruments with sample paths: {sample_count}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())