#!/usr/bin/env python3
"""
Script to remove redundant attributes from YAML field definitions
in format_config.yaml where they match the defaults:
 - size: 1
 - type: "UINT8"
 - default: 0 (including 0x00)
"""

import os
import yaml
import re

def compact_yaml_fields(file_path):
    """
    Load YAML file, remove redundant attributes, and save it back.
    Uses the YAML parser to ensure we maintain valid YAML.
    """
    with open(file_path, 'r') as f:
        yaml_content = yaml.safe_load(f)
    
    # Process the YAML structure recursively
    process_config(yaml_content)
    
    # Write the changes back with indentation preserved and consistent ordering
    with open(file_path, 'w') as f:
        yaml.dump(yaml_content, f, default_flow_style=False, sort_keys=True)
    
    print(f"Updated {file_path} - Compacted field definitions")
    return True

def process_config(config):
    """Process the YAML configuration recursively to remove default values."""
    if not isinstance(config, dict):
        return
    
    # Process all dictionary items
    for key, value in config.items():
        if isinstance(value, dict):
            # Check if this is a field definition with offset
            if 'offset' in value:
                # Remove default values that match the defaults
                if 'size' in value and value['size'] == 1:
                    del value['size']
                if 'type' in value and value['type'] == "UINT8":
                    del value['type']
                if 'default' in value and (value['default'] == 0 or value['default'] == 0x00):
                    del value['default']
            
            # Recursively process nested dictionaries
            process_config(value)
        elif isinstance(value, list):
            # Process lists
            for item in value:
                if isinstance(item, dict):
                    process_config(item)

if __name__ == "__main__":
    # Get the absolute path to the format_config.yaml file
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    config_path = os.path.join(repo_root, 'm8', 'format_config.yaml')
    
    if os.path.exists(config_path):
        compact_yaml_fields(config_path)
    else:
        print(f"Error: Could not find {config_path}")