#!/usr/bin/env python3
"""
Script to move M8EnumValueError from m8/api/__init__.py to m8/core/enums.py
and update all import references in the codebase.
"""
import os
import re
import sys

# The directories to search
DIRS = ['m8', 'tests']

def extract_exception_code():
    """Extract the M8EnumValueError class definition from m8/api/__init__.py."""
    with open('m8/api/__init__.py', 'r') as f:
        content = f.read()
    
    # Regular expression to match the class definition
    pattern = r'class M8EnumValueError\(Exception\):.*?(?=\n\n)'
    match = re.search(pattern, content, re.DOTALL)
    
    if match:
        return match.group(0)
    else:
        raise ValueError("Could not find M8EnumValueError class in m8/api/__init__.py")

def remove_exception_from_api_init(exception_code):
    """Remove the M8EnumValueError class from m8/api/__init__.py."""
    with open('m8/api/__init__.py', 'r') as f:
        content = f.read()
    
    # Replace the exception code with an empty string
    new_content = content.replace(exception_code, '')
    
    with open('m8/api/__init__.py', 'w') as f:
        f.write(new_content)

def add_exception_to_core_enums(exception_code):
    """Add the M8EnumValueError class to m8/core/enums.py."""
    with open('m8/core/enums.py', 'r') as f:
        content = f.read()
    
    # Add the exception code after imports but before other code
    import_section_end = content.find('# Global enum class cache')
    if import_section_end == -1:
        import_section_end = content.find('_ENUM_CLASS_CACHE')
    
    if import_section_end > 0:
        new_content = content[:import_section_end] + '\n' + exception_code + '\n\n' + content[import_section_end:]
        
        with open('m8/core/enums.py', 'w') as f:
            f.write(new_content)
    else:
        print("Could not find appropriate location to insert exception code in m8/core/enums.py")

def update_import_references():
    """Update all import references to M8EnumValueError in the codebase."""
    files_updated = 0
    
    for dir_name in DIRS:
        for root, _, files in os.walk(dir_name):
            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    
                    # Skip the core/enums.py file itself
                    if file_path == 'm8/core/enums.py':
                        continue
                    
                    with open(file_path, 'r') as f:
                        content = f.read()
                    
                    # Replace import patterns
                    updated_content = content
                    
                    # Pattern 1: from m8.api import ..., M8EnumValueError, ...
                    updated_content = re.sub(
                        r'from m8\.api import (.*?)M8EnumValueError(.*?)',
                        r'from m8.api import \1\2',
                        updated_content
                    )
                    
                    # Pattern 2: 'from m8.api import M8EnumValueError'
                    updated_content = re.sub(
                        r'from m8\.api import M8EnumValueError(?:\s*$|\s*#.*$)',
                        r'from m8.core.enums import M8EnumValueError',
                        updated_content
                    )
                    
                    # Pattern 3: Import with M8EnumValueError and others
                    if "from m8.api import" in updated_content and "M8EnumValueError" in updated_content:
                        # Add the import from core.enums if it doesn't exist
                        if "from m8.core.enums import M8EnumValueError" not in updated_content:
                            updated_content = re.sub(
                                r'(from m8\.api import .*?\n)',
                                r'\1from m8.core.enums import M8EnumValueError\n',
                                updated_content
                            )
                    
                    # Check if content was actually changed
                    if updated_content != content:
                        with open(file_path, 'w') as f:
                            f.write(updated_content)
                        files_updated += 1
                        print(f"Updated {file_path}")
    
    return files_updated

def fix_core_enums_imports():
    """Fix imports in m8/core/enums.py to remove circular references."""
    with open('m8/core/enums.py', 'r') as f:
        content = f.read()
    
    # Remove imports of M8EnumValueError from m8.api
    updated_content = re.sub(
        r'from m8\.api import M8EnumValueError\s*\n',
        '',
        content
    )
    
    # Find all instances where M8EnumValueError is used
    pattern = r'raise M8EnumValueError'
    if re.search(pattern, updated_content):
        # Remove the import and use direct reference
        updated_content = updated_content.replace('from m8.api import M8EnumValueError', '')
    
    with open('m8/core/enums.py', 'w') as f:
        f.write(updated_content)

def main():
    """Main function to execute the script."""
    print("Moving M8EnumValueError from m8/api/__init__.py to m8/core/enums.py...")
    
    try:
        # Extract the exception code
        exception_code = extract_exception_code()
        print("Successfully extracted M8EnumValueError class definition")
        
        # Add the exception to core/enums.py
        add_exception_to_core_enums(exception_code)
        print("Added M8EnumValueError to m8/core/enums.py")
        
        # Remove the exception from api/__init__.py
        remove_exception_from_api_init(exception_code)
        print("Removed M8EnumValueError from m8/api/__init__.py")
        
        # Fix imports in core/enums.py
        fix_core_enums_imports()
        print("Fixed imports in m8/core/enums.py")
        
        # Update import references in all files
        files_updated = update_import_references()
        print(f"Updated import references in {files_updated} files")
        
        print("Migration completed successfully!")
        
    except Exception as e:
        print(f"Error: {e}")
        return 1
    
    return 0

if __name__ == '__main__':
    sys.exit(main())