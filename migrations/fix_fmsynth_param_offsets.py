#!/usr/bin/env python3
"""
Migration to fix the parameter offsets for FMSYNTH in format_config.yaml.
There are overlapping offsets in the current config:
- mod_2 (48) overlaps with filter (48)
- mod_3 (49) overlaps with cutoff (49)
- mod_4 (50) overlaps with res (50)

This script will update the offsets for parameters that come after mod_4.
"""

import os
import sys
import yaml

# Ensure we can import from the m8 package
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def load_yaml_file(file_path):
    """Load YAML file"""
    with open(file_path, 'r') as f:
        return yaml.safe_load(f)

def save_yaml_file(file_path, data):
    """Save YAML file with consistent formatting"""
    with open(file_path, 'w') as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=True)

def main():
    """Main function to fix FMSYNTH parameter offsets"""
    # Path to format_config.yaml
    config_path = os.path.join('m8', 'format_config.yaml')
    
    # Load the current config
    config = load_yaml_file(config_path)
    
    # Get the FMSYNTH params
    fmsynth_params = config['instruments']['types']['FMSYNTH']['params']
    
    # Print current configuration
    print("Current FMSYNTH parameter offsets:")
    for param, details in sorted(fmsynth_params.items(), key=lambda x: x[1].get('offset', 0)):
        if 'offset' in details:
            print(f"  {param}: {details['offset']}")
    
    # Define the parameters that need to be adjusted (those after mod_4)
    params_to_adjust = [
        'filter', 'cutoff', 'res', 'amp', 'limit', 'pan', 'dry', 'chorus', 'delay', 'reverb'
    ]
    
    # Mapping of current offsets to new offsets
    offset_adjustments = {
        48: 51,  # filter
        49: 52,  # cutoff
        50: 53,  # res
        51: 54,  # amp
        52: 55,  # limit
        53: 56,  # pan
        54: 57,  # dry
        55: 58,  # chorus
        56: 59,  # delay
        57: 60,  # reverb
    }
    
    # Update the offsets
    for param, details in fmsynth_params.items():
        if param in params_to_adjust and 'offset' in details:
            current_offset = details['offset']
            if current_offset in offset_adjustments:
                details['offset'] = offset_adjustments[current_offset]
    
    # Save the updated config
    save_yaml_file(config_path, config)
    
    # Print updated configuration
    print("\nUpdated FMSYNTH parameter offsets:")
    fmsynth_params = load_yaml_file(config_path)['instruments']['types']['FMSYNTH']['params']
    for param, details in sorted(fmsynth_params.items(), key=lambda x: x[1].get('offset', 0)):
        if 'offset' in details:
            print(f"  {param}: {details['offset']}")
    
    print("\nFMSYNTH parameter offsets have been fixed successfully!")

if __name__ == "__main__":
    main()