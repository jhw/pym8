#!/usr/bin/env python3
"""
Script to remove redundant attributes from YAML field definitions
in format_config.yaml where they match the defaults:
 - size: 1
 - type: "UINT8"
 - default: 0
"""

import os
import yaml
import re

def should_compact_field(field_def):
    """Check if a field definition should be compacted."""
    if not isinstance(field_def, dict):
        return False
    
    needs_compacting = False
    
    # Check for size: 1
    if 'size' in field_def and field_def['size'] == 1:
        needs_compacting = True
        
    # Check for type: "UINT8"
    if 'type' in field_def and field_def['type'] == "UINT8":
        needs_compacting = True
        
    # Check for default: 0
    if 'default' in field_def and field_def['default'] == 0:
        needs_compacting = True
    
    return needs_compacting

def compact_yaml_fields(file_path):
    """
    Load YAML file, remove redundant attributes, and save it back.
    Uses regex to maintain the original formatting.
    """
    with open(file_path, 'r') as f:
        content = f.read()
    
    # First pattern: remove size: 1, type: "UINT8"
    pattern1 = re.compile(r'({[^{}]*?)size: 1, type: "UINT8"(,\s*|[^{}]*?})')
    content = pattern1.sub(r'\1\2', content)
    
    # Second pattern: remove default: 0 with comma
    pattern2 = re.compile(r'({[^{}]*?)default: 0,\s*([^{}]*?})')
    content = pattern2.sub(r'\1\2', content)
    
    # Third pattern: remove default: 0 at the end
    pattern3 = re.compile(r'({[^{}]*?), default: 0(})')
    content = pattern3.sub(r'\1\2', content)
    
    # Fourth pattern: handle simple case of just {offset: X, default: 0}
    pattern4 = re.compile(r'{offset: ([^{}]+), default: 0}')
    content = pattern4.sub(r'{offset: \1}', content)
    
    # Fix any messed up formatting (double commas etc.)
    content = content.replace(", ,", ",")
    content = content.replace(",}", "}")
    
    # Write the changes back
    with open(file_path, 'w') as f:
        f.write(content)
    print(f"Updated {file_path} - Compacted field definitions")
    return True

if __name__ == "__main__":
    # Get the absolute path to the format_config.yaml file
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    config_path = os.path.join(repo_root, 'm8', 'format_config.yaml')
    
    if os.path.exists(config_path):
        compact_yaml_fields(config_path)
    else:
        print(f"Error: Could not find {config_path}")