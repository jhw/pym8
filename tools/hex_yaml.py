#!/usr/bin/env python
"""Script to convert integers in YAML to hex representation."""

import yaml
import sys
import os

class HexInt(int):
    """Integer subclass for representing integers as hex in YAML."""
    pass

def hexint_representer(dumper, data):
    """Custom YAML representer for HexInt that outputs integers as hex."""
    return dumper.represent_scalar('tag:yaml.org,2002:int', hex(data))

def convert_ints_to_hexint(data):
    """Recursively convert integers in data structure to HexInt."""
    if isinstance(data, dict):
        return {k: convert_ints_to_hexint(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [convert_ints_to_hexint(item) for item in data]
    elif isinstance(data, int) and not isinstance(data, bool):
        return HexInt(data)
    else:
        return data

def process_yaml_file(file_path, output_path=None):
    """Process a YAML file to convert integers to hex representation."""
    if output_path is None:
        output_path = file_path
    
    # Register the HexInt representer
    yaml.add_representer(HexInt, hexint_representer)
    
    # Load the YAML file
    with open(file_path, 'r') as file:
        data = yaml.safe_load(file)
    
    # Convert integers to HexInt
    hex_data = convert_ints_to_hexint(data)
    
    # Write the converted data back to the file
    with open(output_path, 'w') as file:
        yaml.dump(hex_data, file, default_flow_style=False, sort_keys=True)
    
    print(f"Converted {file_path} to use hex representation for integers.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python hex_yaml.py <yaml_file> [output_file]")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    if not os.path.exists(input_file):
        print(f"Error: File {input_file} not found.")
        sys.exit(1)
    
    process_yaml_file(input_file, output_file)