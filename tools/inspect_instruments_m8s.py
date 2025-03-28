#!/usr/bin/env python3
import argparse
import os
import sys
import yaml
import logging

from m8.api.project import M8Project
from m8.api.instruments import M8Instrument
from m8.api import M8Block

def hex_dump(data, width=16):
    """Prints data in a readable hex dump format."""
    result = []
    for i in range(0, len(data), width):
        chunk = data[i:i+width]
        hex_values = ' '.join(f"{b:02X}" for b in chunk)
        ascii_values = ''.join(chr(b) if 32 <= b < 127 else '.' for b in chunk)
        result.append(f"{i:08X}  {hex_values:<{width * 3}} |{ascii_values}|")
    return "\n".join(result)

def display_instrument(instrument, index, output_format):
    if output_format == "yaml":
        # Convert to dict and output as YAML with integers as hex
        instrument_dict = instrument.as_dict()
        
        # Custom representer function to format integers as hex
        def represent_int_as_hex(dumper, data):
            if isinstance(data, int):
                # Format as 0xNN
                return dumper.represent_scalar('tag:yaml.org,2002:str', f"0x{data:02X}")
            return dumper.represent_scalar('tag:yaml.org,2002:int', str(data))
            
        # Add the representer to the YAML dumper
        yaml.add_representer(int, represent_int_as_hex)
        
        print(yaml.dump(instrument_dict, sort_keys=False, default_flow_style=False))
    else:  # bytes format
        # Get raw binary data
        raw_data = instrument.write()
        print(f"Instrument: {instrument.name} (Type: {instrument.type}, Index: {index})")
        print(f"Raw binary data ({len(raw_data)} bytes):")
        print(hex_dump(raw_data))

def main():
    parser = argparse.ArgumentParser(description="Inspect instruments in an M8 project file")
    parser.add_argument("file_path", help="Path to the M8 project file (.m8s)")
    parser.add_argument("--format", "-f", choices=["yaml", "bytes"], default="yaml", 
                        help="Output format (yaml or bytes, default: yaml)")
    
    args = parser.parse_args()
    
    # Suppress warnings about unknown instrument types
    logging.getLogger("m8.api.instruments").setLevel(logging.ERROR)
    
    # Check if file exists
    if not os.path.exists(args.file_path):
        print(f"Error: File {args.file_path} does not exist", file=sys.stderr)
        return 1
    
    # Check file extension
    if not args.file_path.lower().endswith(".m8s"):
        print(f"Error: File {args.file_path} does not have .m8s extension", file=sys.stderr)
        return 1
    
    try:
        # Load project
        project = M8Project.read_from_file(args.file_path)
        
        # Find non-empty instruments
        non_empty_instruments = []
        for idx, instrument in enumerate(project.instruments):
            if not isinstance(instrument, M8Block):
                non_empty_instruments.append((idx, instrument))
        
        if not non_empty_instruments:
            print("No non-empty instruments found in the project", file=sys.stderr)
            return 1
        
        print(f"Found {len(non_empty_instruments)} non-empty instruments")
        
        # Iterate through non-empty instruments
        for idx, instrument in non_empty_instruments:
            print(f"\nInstrument {idx}: {instrument.name} (Type: {instrument.type})")
            
            # Prompt user
            while True:
                response = input("Dump instrument details? (y/n/q): ").lower()
                if response == 'y':
                    print("\n" + "="*50)
                    display_instrument(instrument, idx, args.format)
                    print("="*50)
                    break
                elif response == 'n':
                    break
                elif response == 'q':
                    print("Exiting...")
                    return 0
                else:
                    print("Invalid option. Please enter 'y', 'n', or 'q'")
            
        return 0
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())