#!/usr/bin/env python3
import unittest
import os
import sys
import importlib
import pkgutil
import time
from collections import defaultdict

def discover_test_modules(package_name="tests"):
    """Recursively discover all test modules in the given package."""
    package = importlib.import_module(package_name)
    
    for _, name, is_pkg in pkgutil.iter_modules(package.__path__, package.__name__ + '.'):
        if is_pkg:
            # If it's a package, recursively scan it
            discover_test_modules(name)
        else:
            # If it's a module, import it to add its tests to the registry
            importlib.import_module(name)

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

class TimedTestResult(unittest.TextTestResult):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.test_timings = {}

    def startTest(self, test):
        self._start_time = time.time()
        super().startTest(test)

    def stopTest(self, test):
        elapsed = time.time() - self._start_time
        name = self.getDescription(test)
        self.test_timings[name] = elapsed
        super().stopTest(test)

class TimedTextTestRunner(unittest.TextTestRunner):
    def __init__(self, *args, **kwargs):
        kwargs['resultclass'] = TimedTestResult
        super().__init__(*args, **kwargs)
    
    def run(self, test):
        result = super().run(test)
        self.print_timings(result.test_timings)
        return result
    
    def print_timings(self, timings):
        print("\n=== Test Execution Times ===")
        
        # Group by module
        module_timings = defaultdict(list)
        for test_name, elapsed in sorted(timings.items(), key=lambda x: x[1], reverse=True):
            # Extract module name from test description
            parts = test_name.split('.')
            if len(parts) >= 2:
                module = '.'.join(parts[:-1])
                module_timings[module].append((test_name, elapsed))

        # Print overall timings 
        print("\nOverall Test Times (sorted by duration):")
        print("-" * 80)
        for test_name, elapsed in sorted(timings.items(), key=lambda x: x[1], reverse=True):
            print(f"{elapsed:.4f}s - {test_name}")
        
        # Print module summaries
        print("\nModule Summaries:")
        print("-" * 80)
        modules_by_time = sorted(module_timings.items(), 
                                key=lambda x: sum(t[1] for t in x[1]), 
                                reverse=True)
        
        for module, tests in modules_by_time:
            total_time = sum(elapsed for _, elapsed in tests)
            print(f"{module}: {total_time:.4f}s total, {len(tests)} tests")

def run_tests():
    """Discover and run all tests in the tests package with timing information."""
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
    
    # Run the tests with timing
    runner = TimedTextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Clean up any leftover temporary test directories
    clean_temp_test_dirs()
    
    # Return non-zero exit code if tests failed
    return 0 if result.wasSuccessful() else 1

if __name__ == "__main__":
    start_time = time.time()
    exit_code = run_tests()
    total_duration = time.time() - start_time
    print(f"\nTotal test suite execution time: {total_duration:.2f} seconds")
    sys.exit(exit_code)