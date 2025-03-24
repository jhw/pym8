#!/usr/bin/env python3
import os
import re
import sys

# Enum strings to replace
INSTRUMENT_TYPES = ['wavsynth', 'macrosynth', 'sampler']
MODULATOR_TYPES = ['lfo', 'adsr_envelope', 'ahd_envelope', 'drum_envelope', 'trigger_envelope', 'tracking_envelope']

# Patterns for different scenarios

# 1. Replace instrument_type="wavsynth" -> instrument_type="WAVSYNTH"
inst_type_pattern = re.compile(r'(instrument_type=")(' + '|'.join(INSTRUMENT_TYPES) + r')(")|(instrument_type=)(' + '|'.join(INSTRUMENT_TYPES) + r')(\))|(["\']\s*instrument_type["\']\s*:\s*["\'])(' + '|'.join(INSTRUMENT_TYPES) + r')(["\'])')

# 2. Replace modulator_type="lfo" -> modulator_type="LFO" 
mod_type_pattern = re.compile(r'(modulator_type=")(' + '|'.join(MODULATOR_TYPES) + r')(")|(modulator_type=)(' + '|'.join(MODULATOR_TYPES) + r')(\))|(["\']\s*modulator_type["\']\s*:\s*["\'])(' + '|'.join(MODULATOR_TYPES) + r')(["\'])')

# 3. Replace assertions like assertEqual(mod.modulator_type, "lfo") -> assertEqual(mod.modulator_type, "LFO")
assert_pattern = re.compile(r'(assertEqual\([^,]+,\s*["\'])(' + '|'.join(INSTRUMENT_TYPES + MODULATOR_TYPES) + r')(["\'])')

# 4. Fix EnumErrorHandling specific test case
enum_error_pattern = re.compile(r'(M8InstrumentParams\.from_config\(")(' + '|'.join(INSTRUMENT_TYPES) + r')(")|(M8InstrumentParams\.from_config\()(' + '|'.join(INSTRUMENT_TYPES) + r')(\))')

def process_file(file_path):
    """Process a single file, updating enum strings."""
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Function to uppercase the enum string in a match
        def uppercase_match(match):
            if match.group(2):  # First regex group - quoted string
                return match.group(1) + match.group(2).upper() + match.group(3)
            elif match.group(5):  # Second regex group - unquoted string
                return match.group(4) + match.group(5).upper() + match.group(6)
            elif match.group(8):  # Third regex group - dict format
                return match.group(7) + match.group(8).upper() + match.group(9)
            return match.group(0)  # No change if no match

        def uppercase_assert_match(match):
            # For assertion patterns
            return match.group(1) + match.group(2).upper() + match.group(3)
            
        # Replace all patterns
        modified_content = inst_type_pattern.sub(uppercase_match, content)
        modified_content = mod_type_pattern.sub(uppercase_match, modified_content)
        modified_content = assert_pattern.sub(uppercase_assert_match, modified_content)
        modified_content = enum_error_pattern.sub(uppercase_match, modified_content)
        
        # Only write back if changes were made
        if modified_content != content:
            print(f"Updating {file_path}")
            with open(file_path, 'w') as f:
                f.write(modified_content)
            return True
        return False
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return False

def process_directory(dir_path, extensions=['.py']):
    """Recursively process all Python files in a directory."""
    files_changed = 0
    
    for root, dirs, files in os.walk(dir_path):
        for file in files:
            if any(file.endswith(ext) for ext in extensions):
                file_path = os.path.join(root, file)
                if process_file(file_path):
                    files_changed += 1
    
    return files_changed

if __name__ == "__main__":
    if len(sys.argv) > 1:
        target_dir = sys.argv[1]
    else:
        target_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'tests')
    
    print(f"Processing files in {target_dir}")
    files_changed = process_directory(target_dir)
    print(f"Updated {files_changed} files")