#!/usr/bin/env python3
import argparse
import os
import sys
import yaml
import logging

from m8.api.project import M8Project
from m8.api.instruments import M8Instrument
from m8.api import M8Block

def display_instrument(instrument, index):
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

def main():
    parser = argparse.ArgumentParser(description="Inspect instruments in an M8 project file")
    parser.add_argument("file_path", help="Path to the M8 project file (.m8s)")
    
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
                    display_instrument(instrument, idx)
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