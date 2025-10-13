#!/usr/bin/env python3
import unittest
import os
import sys
import importlib
import pkgutil

def discover_test_modules(package_name="tests"):
    """Recursively discover all test modules in the given package."""
    package = importlib.import_module(package_name)

    for _, name, is_pkg in pkgutil.iter_modules(package.__path__, package.__name__ + '.'):
        if is_pkg:
            # If it's a package, recursively scan it
            discover_test_modules(name)
        else:
            # If it's a module, import it to add its tests to the registry
            try:
                importlib.import_module(name)
            except ImportError as e:
                print(f"ERROR: Failed to import test module {name}: {e}", file=sys.stderr)
                raise

def clean_temp_test_dirs():
    """Clean up temporary test directories created by tests."""
    tmp_dir = os.path.join(os.getcwd(), "tmp")
    if not os.path.exists(tmp_dir):
        return
        
    import shutil
    import re
    
    # Pattern for test directories
    test_dir_patterns = [
        r"test_bake_chains_\d+",
        r"test_concat_phrases_\d+"
    ]
    
    for item in os.listdir(tmp_dir):
        item_path = os.path.join(tmp_dir, item)
        if os.path.isdir(item_path):
            for pattern in test_dir_patterns:
                if re.match(pattern, item):
                    try:
                        print(f"Cleaning up test directory: {item_path}")
                        shutil.rmtree(item_path)
                    except Exception as e:
                        print(f"Failed to remove {item_path}: {e}")

def run_tests():
    """Discover and run all tests in the tests package."""
    # Ensure the current directory is in the Python path
    sys.path.insert(0, os.getcwd())
    
    # Create a test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Discover tests in the tests package
    discover_test_modules()
    
    # Or use the discover method as an alternative
    discovered_tests = loader.discover('tests', pattern='*.py')
    suite.addTest(discovered_tests)
    
    # Run the tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Clean up any leftover temporary test directories
    clean_temp_test_dirs()
    
    # Return non-zero exit code if tests failed
    return 0 if result.wasSuccessful() else 1

if __name__ == "__main__":
    sys.exit(run_tests())