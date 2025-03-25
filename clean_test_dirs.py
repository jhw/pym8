#!/usr/bin/env python3
"""
Script to clean up temporary test directories created by tests.

This script can be run directly to clean up these directories:
python clean_test_dirs.py
"""

import os
import re
import shutil

def clean_temp_test_dirs():
    """Clean up temporary test directories created by tests."""
    tmp_dir = os.path.join(os.getcwd(), "tmp")
    if not os.path.exists(tmp_dir):
        print("No tmp directory found.")
        return 0
        
    # Pattern for test directories
    test_dir_patterns = [
        r"test_bake_chains_\d+",
        r"test_concat_phrases_\d+"
    ]
    
    cleaned = 0
    for item in os.listdir(tmp_dir):
        item_path = os.path.join(tmp_dir, item)
        if os.path.isdir(item_path):
            for pattern in test_dir_patterns:
                if re.match(pattern, item):
                    try:
                        print(f"Cleaning up test directory: {item_path}")
                        shutil.rmtree(item_path)
                        cleaned += 1
                    except Exception as e:
                        print(f"Failed to remove {item_path}: {e}")
    
    if cleaned == 0:
        print("No test directories found to clean up.")
    else:
        print(f"Cleaned up {cleaned} test directories.")
    
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(clean_temp_test_dirs())