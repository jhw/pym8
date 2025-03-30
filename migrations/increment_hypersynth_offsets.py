#!/usr/bin/env python3

import os
import sys
import yaml

def increment_hypersynth_offsets():
    """Increment all HyperSynth parameter offsets by 12 in format_config.yaml"""
    # Get the absolute path to the format_config.yaml file
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    config_path = os.path.join(project_root, 'm8', 'format_config.yaml')
    
    # Read the YAML file
    print(f"Reading configuration from {config_path}")
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    # Find the HyperSynth section
    hypersynth_config = config['instruments']['types']['HYPERSYNTH']['params']
    
    # Store original values for verification
    original_offsets = {}
    for param, param_config in hypersynth_config.items():
        if 'offset' in param_config:
            original_offsets[param] = param_config['offset']
    
    # Increment all offsets by 12
    print("Incrementing HyperSynth parameter offsets by 12:")
    for param, param_config in hypersynth_config.items():
        if 'offset' in param_config:
            old_offset = param_config['offset']
            param_config['offset'] = old_offset + 12
            print(f"  {param}: {old_offset} -> {param_config['offset']}")
    
    # Write the updated YAML back to the file
    print(f"Writing updated configuration to {config_path}")
    with open(config_path, 'w') as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=True)
    
    # Verify the changes
    print("\nVerification:")
    with open(config_path, 'r') as f:
        updated_config = yaml.safe_load(f)
    
    hypersynth_config = updated_config['instruments']['types']['HYPERSYNTH']['params']
    verification_passed = True
    
    for param, param_config in hypersynth_config.items():
        if 'offset' in param_config:
            if param in original_offsets:
                expected = original_offsets[param] + 12
                actual = param_config['offset']
                if expected != actual:
                    print(f"  ERROR: {param} expected {expected}, got {actual}")
                    verification_passed = False
    
    if verification_passed:
        print("  All offsets incremented correctly")
    else:
        print("  Verification failed")
        sys.exit(1)
    
    print("\nMigration completed successfully")

if __name__ == "__main__":
    increment_hypersynth_offsets()