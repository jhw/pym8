#!/usr/bin/env python3
"""
Script to move utility modules from m8/api/utils to m8/core/utils
and update all import references in the codebase.
"""
import os
import re
import shutil
import sys

# The directories to search for import references
DIRS = ['m8', 'tests']

def create_core_utils_directory():
    """Create the m8/core/utils directory if it doesn't exist."""
    os.makedirs('m8/core/utils', exist_ok=True)
    
    # Create an empty __init__.py file if it doesn't exist
    init_path = 'm8/core/utils/__init__.py'
    if not os.path.exists(init_path):
        with open(init_path, 'w') as f:
            f.write('"""Core utility modules for the M8 library."""')

def copy_utils_files():
    """Copy all files from m8/api/utils to m8/core/utils."""
    # Get all Python files in the api/utils directory
    utils_files = []
    for file in os.listdir('m8/api/utils'):
        if file.endswith('.py') or file == 'README.md':
            utils_files.append(file)
    
    # Copy each file to the new location
    for file in utils_files:
        source = os.path.join('m8/api/utils', file)
        destination = os.path.join('m8/core/utils', file)
        
        # Don't overwrite existing files
        if not os.path.exists(destination):
            shutil.copy2(source, destination)
            print(f"Copied {source} to {destination}")

def update_import_references():
    """Update all import references from m8.api.utils to m8.core.utils."""
    files_updated = 0
    
    for dir_name in DIRS:
        for root, _, files in os.walk(dir_name):
            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    
                    with open(file_path, 'r') as f:
                        content = f.read()
                    
                    # Replace different import patterns
                    updated_content = content
                    
                    # Pattern 1: from m8.api.utils import ...
                    updated_content = re.sub(
                        r'from m8\.api\.utils import',
                        r'from m8.core.utils import',
                        updated_content
                    )
                    
                    # Pattern 2: from m8.api.utils.xxx import ...
                    updated_content = re.sub(
                        r'from m8\.api\.utils\.([\w_]+) import',
                        r'from m8.core.utils.\1 import',
                        updated_content
                    )
                    
                    # Pattern 3: import m8.api.utils.xxx
                    updated_content = re.sub(
                        r'import m8\.api\.utils\.([\w_]+)',
                        r'import m8.core.utils.\1',
                        updated_content
                    )
                    
                    # Pattern 4: import m8.api.utils
                    updated_content = re.sub(
                        r'import m8\.api\.utils',
                        r'import m8.core.utils',
                        updated_content
                    )
                    
                    # Check if content was actually changed
                    if updated_content != content:
                        with open(file_path, 'w') as f:
                            f.write(updated_content)
                        files_updated += 1
                        print(f"Updated {file_path}")
    
    return files_updated

def update_api_init():
    """Update m8/api/__init__.py to import from m8.core.utils."""
    file_path = 'm8/api/__init__.py'
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Replace the import statements
    updated_content = re.sub(
        r'from m8\.api\.utils\.bit_utils import',
        r'from m8.core.utils.bit_utils import',
        content
    )
    
    updated_content = re.sub(
        r'from m8\.api\.utils\.string_utils import',
        r'from m8.core.utils.string_utils import',
        updated_content
    )
    
    updated_content = re.sub(
        r'from m8\.api\.utils\.json_utils import',
        r'from m8.core.utils.json_utils import',
        updated_content
    )
    
    # Write the updated content back
    if updated_content != content:
        with open(file_path, 'w') as f:
            f.write(updated_content)
        print(f"Updated {file_path}")

def create_api_utils_redirects():
    """
    Create redirect imports in m8/api/utils to maintain backward compatibility.
    
    This is important to avoid breaking existing code that still imports from m8.api.utils.
    """
    # Create a new __init__.py that redirects imports
    init_path = 'm8/api/utils/__init__.py'
    with open(init_path, 'w') as f:
        f.write('"""Utility modules for the M8 API (redirected to m8.core.utils)."""\n\n')
        f.write('# Re-export from core.utils for backward compatibility\n')
        f.write('from m8.core.utils.bit_utils import *\n')
        f.write('from m8.core.utils.string_utils import *\n')
        f.write('from m8.core.utils.json_utils import *\n')
    
    # Create redirect files for each utility module
    for module in ['bit_utils', 'string_utils', 'json_utils']:
        module_path = f'm8/api/utils/{module}.py'
        with open(module_path, 'w') as f:
            f.write(f'"""Redirect module for backward compatibility."""\n\n')
            f.write(f'# Re-export from core.utils\n')
            f.write(f'from m8.core.utils.{module} import *\n')
    
    print("Created backward compatibility redirects in m8/api/utils")

def main():
    """Main function to execute the script."""
    print("Moving utility modules from m8/api/utils to m8/core/utils...")
    
    try:
        # Step 1: Create the target directory
        create_core_utils_directory()
        print("Created m8/core/utils directory")
        
        # Step 2: Copy the files
        copy_utils_files()
        
        # Step 3: Update import references throughout the codebase
        files_updated = update_import_references()
        print(f"Updated import references in {files_updated} files")
        
        # Step 4: Update m8/api/__init__.py specifically
        update_api_init()
        
        # Step 5: Create backward compatibility redirects
        create_api_utils_redirects()
        
        print("\nMigration completed successfully!")
        print("\nNote: The original m8/api/utils files have not been deleted.")
        print("You can safely delete them after testing if everything works correctly.")
        
    except Exception as e:
        print(f"Error: {e}")
        return 1
    
    return 0

if __name__ == '__main__':
    sys.exit(main())