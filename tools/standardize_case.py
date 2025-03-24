#!/usr/bin/env python3
"""Standardize instrument and modulator type names to uppercase."""

import re
import sys
from string_substitution import process_directory, create_pattern

def uppercase_type_processor(match):
    """Convert instrument/modulator type match to uppercase."""
    # Full match is needed since different capture groups might match
    full_match = match.group(0)
    
    # The match groups are complex - we need to identify which one matched
    for i in range(1, len(match.groups()) + 1, 3):
        if i+1 < len(match.groups()) + 1 and match.group(i+1):
            # Found a match - return with the middle part uppercased
            return match.group(i) + match.group(i+1).upper() + match.group(i+2)
    
    # If we get here, something unexpected happened
    return full_match

if __name__ == "__main__":
    # Get base directory from command line or use current directory
    base_dir = sys.argv[1] if len(sys.argv) > 1 else '..'
    
    # Pattern for instrument_type='WAVSYNTH' or modulator_type='LFO' etc.
    # This matches:
    # 1. instrument_type='WAVSYNTH'
    # 2. modulator_type='LFO'
    # 3. instrument_type="WAVSYNTH"
    # 4. instrument_type=WAVSYNTH (in YAML)
    # 5. "instrument_type": "WAVSYNTH"
    # 6. 'modulator_type': 'LFO'
    
    # Instrument types to standardize
    instrument_types = ['wavsynth', 'macrosynth', 'sampler']
    inst_pattern_strings = [
        r'(instrument_type\s*=\s*["\'])(' + '|'.join(instrument_types) + r')(["\'])',
        r'(instrument_type\s*=\s*)(' + '|'.join(instrument_types) + r')(\s)',
        r'(["\']\s*instrument_type["\']\s*:\s*["\'])(' + '|'.join(instrument_types) + r')(["\'])',
    ]
    
    # Modulator types to standardize
    modulator_types = [
        'lfo', 'ahd_envelope', 'adsr_envelope', 'drum_envelope', 
        'trigger_envelope', 'tracking_envelope'
    ]
    mod_pattern_strings = [
        r'(modulator_type\s*=\s*["\'])(' + '|'.join(modulator_types) + r')(["\'])',
        r'(modulator_type\s*=\s*)(' + '|'.join(modulator_types) + r')(\s)',
        r'(["\']\s*modulator_type["\']\s*:\s*["\'])(' + '|'.join(modulator_types) + r')(["\'])',
    ]
    
    # Create regex patterns
    patterns = [re.compile(p, re.IGNORECASE) for p in inst_pattern_strings + mod_pattern_strings]
    
    # Process all files
    print(f"Processing {base_dir} for case standardization...")
    processors = [uppercase_type_processor] * len(patterns)
    changed = process_directory(base_dir, patterns, processors)
    print(f"Done! Modified {changed} files.")
    
    print("\nUpdating fallback lookup code to enforce uppercase...")
    
    # In config.py, simplify the lookup to only use uppercase
    config_pattern_strings = [
        # Pattern for modulator_data function
        r'(# Try uppercase version first\s+lookup_type = modulator_type\.upper\(\).+?# Try lowercase version as fallback\s+lookup_type = modulator_type\.lower\(\).+?if lookup_type in.+?\s+return.+?\s+)',
        
        # Pattern for modulator_type_id function
        r'(# Try uppercase version first\s+lookup_type = modulator_type\.upper\(\).+?if \'modulators\'.+?\s+return.+?\s+# Try lowercase version as fallback.+?lookup_type = modulator_type\.lower\(\).+?if \'modulators\'.+?\s+return.+?\s+)',
        
        # Pattern for instrument_type_id function
        r'(# Try uppercase version first\s+lookup_type = instrument_type\.upper\(\).+?if \(\'instruments\'.+?\s+return.+?\s+# Try lowercase version as fallback.+?lookup_type = instrument_type\.lower\(\).+?if \(\'instruments\'.+?\s+return.+?\s+)',
    ]
    
    # Define replacement patterns - just keep the uppercase version
    config_replacements = [
        # For modulator_data
        r'# Always use uppercase for lookup\n        lookup_type = modulator_type.upper() if isinstance(modulator_type, str) else modulator_type\n        if lookup_type in modulator_types:\n            return modulator_types[lookup_type]\n            \n        ',
        
        # For modulator_type_id
        r'# Always use uppercase for lookup\n    lookup_type = modulator_type.upper() if isinstance(modulator_type, str) else modulator_type\n    \n    if \'modulators\' in config and \'types\' in config[\'modulators\'] and lookup_type in config[\'modulators\'][\'types\']:\n        type_id = config[\'modulators\'][\'types\'][lookup_type][\'id\']\n        if isinstance(type_id, str) and type_id.startswith(\'0x\'):\n            return int(type_id, 16)\n        return type_id\n        \n    ',
        
        # For instrument_type_id
        r'# Always use uppercase for lookup\n    lookup_type = instrument_type.upper() if isinstance(instrument_type, str) else instrument_type\n    \n    if (\'instruments\' in config and \'types\' in config[\'instruments\'] and \n        lookup_type in config[\'instruments\'][\'types\']):\n        type_id = config[\'instruments\'][\'types\'][lookup_type][\'type_id\']\n        if isinstance(type_id, str) and type_id.startswith(\'0x\'):\n            return int(type_id, 16)\n        return type_id\n        \n    ',
    ]
    
    # Direct replacements in config.py
    import os
    config_path = os.path.join(base_dir, 'm8', 'config.py')
    
    with open(config_path, 'r') as f:
        content = f.read()
    
    modified_content = content
    for pattern, replacement in zip(config_pattern_strings, config_replacements):
        modified_content = re.sub(pattern, replacement, modified_content, flags=re.DOTALL)
    
    if modified_content != content:
        print(f"Updating {config_path}")
        with open(config_path, 'w') as f:
            f.write(modified_content)
            
    # Fix line 228 in instruments.py where default is lowercase
    instruments_path = os.path.join(base_dir, 'm8', 'api', 'instruments.py')
    
    with open(instruments_path, 'r') as f:
        content = f.read()
    
    # Replace "wavsynth" with "WAVSYNTH" in line 229
    modified_content = re.sub(r'(instrument_type = )"wavsynth"', r'\1"WAVSYNTH"', content)
    
    if modified_content != content:
        print(f"Updating {instruments_path}")
        with open(instruments_path, 'w') as f:
            f.write(modified_content)
            
    print("Done with config updates!")