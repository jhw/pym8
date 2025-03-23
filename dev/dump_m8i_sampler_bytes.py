#!/usr/bin/env python

import os
import sys
import argparse
from m8.config import get_offset, get_instrument_types, get_instrument_modulators_offset
import yaml

def hex_dump(data, start=0, end=None, bytes_per_line=16):
    """
    Creates a hex dump of binary data with address, hex values, and ASCII representation.
    
    Args:
        data: Binary data to dump
        start: Starting offset to display
        end: Ending offset to display (exclusive, None for all data)
        bytes_per_line: Number of bytes to display per line
    """
    if end is None:
        end = len(data)
    
    result = []
    
    for i in range(start, end, bytes_per_line):
        # Current line of bytes to process
        chunk = data[i:min(i+bytes_per_line, end)]
        
        # Format the address
        address = f"{i:08x}"
        
        # Format the hex values
        hex_values = " ".join(f"{b:02x}" for b in chunk)
        # Pad hex values to align ASCII representation
        hex_padding = " " * (3 * (bytes_per_line - len(chunk)))
        
        # Format the ASCII representation
        ascii_repr = ""
        for b in chunk:
            if 32 <= b <= 126:  # Printable ASCII
                ascii_repr += chr(b)
            else:
                ascii_repr += "."
        
        # Combine all parts
        line = f"{address}:  {hex_values}{hex_padding}  |{ascii_repr}|"
        result.append(line)
    
    return "\n".join(result)

def load_m8i_file(file_path):
    """
    Load an M8 instrument file (.m8i) and return its binary data.
    """
    with open(file_path, "rb") as f:
        return f.read()

def get_instrument_type(data):
    """
    Determine the instrument type from binary data.
    Returns the instrument type name and ID.
    """
    # Type ID is at offset 0
    type_id = data[0]
    instr_types = get_instrument_types()
    
    if type_id in instr_types:
        return instr_types[type_id], type_id
    else:
        return f"Unknown (0x{type_id:02x})", type_id

def dump_m8i(file_path):
    """
    Load an M8 instrument file, determine instrument type,
    and dump up to the modulators offset.
    """
    try:
        full_data = load_m8i_file(file_path)
        file_size = len(full_data)
        print(f"Original file size: {file_size} bytes")
        
        # Get metadata offset from config
        try:
            metadata_offset = get_offset("metadata")
            print(f"Metadata offset: 0x{metadata_offset:02x} ({metadata_offset})")
        except ValueError:
            print("Could not find metadata offset in config, using default 0x0E")
            metadata_offset = 0x0E
        
        # Truncate data at metadata offset, keeping data after the offset
        data = full_data[metadata_offset:]
        
        # Get instrument type from the first byte of the data after metadata
        instr_type, type_id = get_instrument_type(data)
        print(f"\nInstrument type: {instr_type} (ID: 0x{type_id:02x})")
        
        # Get modulators offset from config
        try:
            modulators_offset = get_instrument_modulators_offset()
            print(f"Modulators offset: 0x{modulators_offset:02x} ({modulators_offset})")
        except ValueError:
            print(f"Could not determine modulators offset, defaulting to 63")
            modulators_offset = 63  # Default offset for all instrument types
        
        # Dump only up to the modulators offset within the instrument data
        print(f"\nInstrument data size (up to modulators): {modulators_offset} bytes")
        print(f"\nHexdump of instrument data (after metadata offset) up to instrument's modulators section:")
        print(hex_dump(data, start=0, end=modulators_offset))
        
        # Ensure this is a sampler instrument
        if instr_type != "sampler":
            raise ValueError(f"This script requires a sampler instrument, but found: {instr_type}")
        
        # Load the format config to get the sample path offset
        config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 
                                  'm8', 'format_config.yaml')
        with open(config_path, 'r') as config_file:
            config = yaml.safe_load(config_file)
        
        # Get sample path offset and size from config
        sample_path_offset = config['instruments']['sampler']['sample_path']['offset']
        sample_path_size = config['instruments']['sampler']['sample_path']['size']
        
        # Calculate the section end points
        modulators_to_sample_path_size = sample_path_offset - modulators_offset
        
        print(f"\nModulators section size (up to sample path): {modulators_to_sample_path_size} bytes")
        print(f"Sample path offset: 0x{sample_path_offset:02x} ({sample_path_offset})")
        
        # Dump from the modulators offset to the sample path offset
        print(f"\nHexdump of instrument modulators section (up to sample path):")
        print(hex_dump(data, start=modulators_offset, end=sample_path_offset))
        
        # Dump just the sample path section
        print(f"\nSample path section size: {sample_path_size} bytes")
        print(f"Sample path end offset: 0x{sample_path_offset + sample_path_size:02x} ({sample_path_offset + sample_path_size})")
        print(f"\nHexdump of sample path section (just the path buffer):")
        print(hex_dump(data, start=sample_path_offset, end=sample_path_offset + sample_path_size))
        
    except FileNotFoundError:
        print(f"Error: File not found: {file_path}")
        return 1
    except Exception as e:
        print(f"Error: {str(e)}")
        return 1
    
    return 0

def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(description="Dump M8 instrument file (.m8i) up to modulators offset")
    parser.add_argument("file_path", nargs="?", default=os.path.join("dev", "303SAMPLER.m8i"),
                        help="Path to M8 instrument file (.m8i)")
    
    args = parser.parse_args()
    
    return dump_m8i(args.file_path)

if __name__ == "__main__":
    sys.exit(main())
