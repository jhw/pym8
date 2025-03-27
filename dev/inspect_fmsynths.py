#!/usr/bin/env python
"""
Script to inspect FMSYNTHS m8i files for sample paths.
Iterates through all m8i files in the directory and checks if they contain sample paths.
Extracts the following parameter bytes:
- 1 byte at offset 0x18+13-5 as algo
- 4 bytes before 0x18+13 as shapes (hex)
- 8 bytes from offset 0x18+13 as params 1 (decimal integers)
- 8 bytes after params 1 as params 2 (hex)
- 4 bytes after params 2 as params 3 (hex)
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
    
    if len(data) < 0x18 + 13 + 20:  # Need at least 0x18 + 13 - 5 + 8 + 8 + 4 bytes for algo, shapes, params1, params2, and params3
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
    
    # Calculate offset for params1
    params1_offset = 0x18 + 13  # Adding 13 to the offset
    
    # Extract 1 byte before shapes for algo
    algo_offset = params1_offset - 5  # 5 bytes before params1 (1 before shapes)
    algo_byte = data[algo_offset:algo_offset+1]
    algo_hex = f"{algo_byte[0]:02X}"
    
    # Extract 4 bytes before params1 for shapes
    shapes_offset = params1_offset - 4  # 4 bytes before params1
    shapes_bytes = data[shapes_offset:shapes_offset+4]
    shapes_hex = " ".join([f"{b:02X}" for b in shapes_bytes])
    
    # Extract 8 bytes at offset 0x18+13 for params1
    params1_bytes = data[params1_offset:params1_offset+8]
    # Format as integers with 2-figure formatting
    params1_hex = " ".join([f"{b:02d}" for b in params1_bytes])
    
    # Extract 8 bytes after params1 for params2
    params2_offset = params1_offset + 8  # Right after params1
    params2_bytes = data[params2_offset:params2_offset+8]
    params2_hex = " ".join([f"{b:02X}" for b in params2_bytes])
    
    # Extract 4 bytes after params2 for params3
    params3_offset = params2_offset + 8  # Right after params2
    params3_bytes = data[params3_offset:params3_offset+4]
    params3_hex = " ".join([f"{b:02X}" for b in params3_bytes])
    
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
        'algo': algo_hex,
        'shapes': shapes_hex,
        'params1': params1_hex,
        'params2': params2_hex,
        'params3': params3_hex,
        'sample_path': sample_path,
        'sample_path_offset': sample_path_offset,
        'file_size': len(data),
        'has_sample_path': bool(sample_path)
    }

def main():
    """Main function to inspect FMSYNTHS directory"""
    if len(sys.argv) < 2:
        print("Usage: python inspect_fmsynths.py <FMSYNTHS_directory> [--detailed]")
        return 1
    
    base_dir = Path(sys.argv[1])
    detailed = "--detailed" in sys.argv
    
    if not base_dir.exists():
        print(f"Error: Directory {base_dir} does not exist")
        return 1
    
    print("\nInspecting FMSYNTHS instruments for sample paths\n")
    print(f"{'File Name':<20} {'Algo':<6} {'Shapes':<15} {'Params 1':<25} {'Params 2':<25} {'Params 3':<15} {'Sample Path':<10}")
    print("-" * 118)
    
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
        
        # Print the information
        sample_path = info['sample_path']
        if sample_path:
            sample_count += 1
            instruments_with_samples.append((m8i_file, info, data))
            
        # Show True/False for sample path
        has_sample = "True" if info['has_sample_path'] else "False"
            
        print(f"{m8i_file.name:<20} {info['algo']:<6} {info['shapes']:<15} {info['params1']:<25} {info['params2']:<25} {info['params3']:<15} {has_sample:<10}")
    
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
            print(f"Algo: {info['algo']}")
            print(f"Shapes: {info['shapes']}")
            print(f"Params 1: {info['params1']}")
            print(f"Params 2: {info['params2']}")
            print(f"Params 3: {info['params3']}")
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