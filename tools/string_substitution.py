#!/usr/bin/env python3
import os
import re
import sys

def create_pattern(strings, pattern_template):
    """Create a regex pattern from a list of strings and a template."""
    joined_strings = '|'.join(strings)
    return re.compile(pattern_template.replace('STRING_PLACEHOLDER', joined_strings))

def process_file(file_path, patterns, processors):
    """Process a single file using multiple patterns and their processors.
    
    Args:
        file_path: Path to the file to process
        patterns: List of regex patterns
        processors: List of processor functions, one for each pattern
    
    Returns:
        bool: True if file was changed, False otherwise
    """
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        modified_content = content
        for pattern, processor in zip(patterns, processors):
            modified_content = pattern.sub(processor, modified_content)
        
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

def process_directory(dir_path, patterns, processors, extensions=['.py']):
    """Recursively process all files with given extensions in a directory.
    
    Args:
        dir_path: Directory to process
        patterns: List of regex patterns
        processors: List of processor functions, one for each pattern
        extensions: List of file extensions to process
    
    Returns:
        int: Number of files changed
    """
    files_changed = 0
    
    for root, dirs, files in os.walk(dir_path):
        for file in files:
            if any(file.endswith(ext) for ext in extensions):
                file_path = os.path.join(root, file)
                if process_file(file_path, patterns, processors):
                    files_changed += 1
    
    return files_changed

# Common processor functions

def uppercase_match(match, group_indices=(2, 5, 8)):
    """Process a match by uppercasing specific groups.
    
    Args:
        match: The regex match object
        group_indices: Tuple of group indices to uppercase (matched content)
                       with the preceding and following groups
    
    Returns:
        str: The processed string with uppercased content
    """
    for i in group_indices:
        if i < len(match.groups()) + 1 and match.group(i):
            return match.group(i-1) + match.group(i).upper() + match.group(i+1)
    return match.group(0)  # No change if no match

def lowercase_match(match, group_indices=(2, 5, 8)):
    """Process a match by lowercasing specific groups."""
    for i in group_indices:
        if i < len(match.groups()) + 1 and match.group(i):
            return match.group(i-1) + match.group(i).lower() + match.group(i+1)
    return match.group(0)  # No change if no match

# Example pattern templates for common cases
ATTR_PATTERN_TEMPLATE = r'(ATTR_NAME=")(' + 'STRING_PLACEHOLDER' + r')(")|(ATTR_NAME=)(' + 'STRING_PLACEHOLDER' + r')(\))|(["\']\s*ATTR_NAME["\']\s*:\s*["\'])(' + 'STRING_PLACEHOLDER' + r')(["\'])'
ASSERT_PATTERN_TEMPLATE = r'(assertEqual\([^,]+,\s*["\'])(' + 'STRING_PLACEHOLDER' + r')(["\'])'

if __name__ == "__main__":
    print("String substitution tool - use this module by importing it")
    print("Example usage:")
    print("  from tools.string_substitution import create_pattern, process_directory, uppercase_match")
    print("  strings = ['foo', 'bar', 'baz']")
    print("  pattern = create_pattern(strings, r'(value=")(' + 'STRING_PLACEHOLDER' + r')(")')")
    print("  process_directory('/path/to/dir', [pattern], [uppercase_match])")