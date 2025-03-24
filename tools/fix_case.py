#!/usr/bin/env python3
"""
Example utility using the string_substitution module to fix case in the codebase.

This script can be used to:
1. Convert enum strings to uppercase (similar to the previous fix_enum_strings.py)
2. Convert enum strings to lowercase if needed
"""

import os
import sys
import re
from string_substitution import (
    create_pattern, 
    process_directory,
    uppercase_match,
    lowercase_match,
    ATTR_PATTERN_TEMPLATE,
    ASSERT_PATTERN_TEMPLATE
)

def fix_case(strings, attribute_name, target_dir, to_uppercase=True):
    """Fix case for a list of strings associated with a specific attribute.
    
    Args:
        strings: List of strings to search for
        attribute_name: Name of the attribute (e.g., 'instrument_type', 'modulator_type')
        target_dir: Directory to process
        to_uppercase: If True, convert to uppercase; if False, convert to lowercase
    
    Returns:
        int: Number of files changed
    """
    # Create patterns for attribute assignments and assertions
    attr_pattern = create_pattern(
        strings, 
        ATTR_PATTERN_TEMPLATE.replace('ATTR_NAME', attribute_name)
    )
    
    assert_pattern = create_pattern(
        strings,
        ASSERT_PATTERN_TEMPLATE
    )
    
    # Custom pattern for constructor calls if needed
    constructor_pattern = create_pattern(
        strings,
        r'(M8\w+Params\.from_config\(")(' + 'STRING_PLACEHOLDER' + r')(")|(M8\w+Params\.from_config\()(' + 'STRING_PLACEHOLDER' + r')(\))'
    )
    
    # Choose the right processor function
    processor = uppercase_match if to_uppercase else lowercase_match
    
    # Process all patterns
    patterns = [attr_pattern, assert_pattern, constructor_pattern]
    processors = [processor] * len(patterns)
    
    return process_directory(target_dir, patterns, processors)

if __name__ == "__main__":
    # Example usage - convert instrument types to uppercase
    instrument_types = ['wavsynth', 'macrosynth', 'sampler']
    modulator_types = ['lfo', 'adsr_envelope', 'ahd_envelope', 'drum_envelope', 'trigger_envelope', 'tracking_envelope']
    
    if len(sys.argv) > 1:
        target_dir = sys.argv[1]
    else:
        target_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'tests')
        
    operation = "uppercase" if len(sys.argv) <= 2 else sys.argv[2].lower()
    to_uppercase = operation != "lowercase"
    
    print(f"Processing files in {target_dir} - Converting to {operation}")
    
    # Fix instrument types
    files_changed = fix_case(instrument_types, 'instrument_type', target_dir, to_uppercase)
    print(f"Updated {files_changed} files for instrument_type")
    
    # Fix modulator types
    files_changed = fix_case(modulator_types, 'modulator_type', target_dir, to_uppercase)
    print(f"Updated {files_changed} files for modulator_type")