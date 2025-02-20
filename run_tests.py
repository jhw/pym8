import os
import unittest

def find_and_run_tests(root_dirs):
    suite = unittest.TestSuite()
    print ()
    for root_dir in root_dirs:
        for root, _, files in os.walk(root_dir):
            for file in files:
                if file.endswith('.py'):
                    full_path = os.path.join(root, file)
                    module_name = full_path.replace(os.sep, '.')[:-3] 
                    module = __import__(module_name, fromlist=[''])
                    for name in dir(module):
                        obj = getattr(module, name)
                        if (isinstance(obj, type) and
                            issubclass(obj, unittest.TestCase)):
                            print (str(obj)[1:-1].split(" ")[-1][1:-1])
                            suite.addTest(unittest.TestLoader().loadTestsFromTestCase(obj))
    print ()
    unittest.TextTestRunner().run(suite)

if __name__ == "__main__":
    try:
        find_and_run_tests(["tests"])
    except RuntimeError as error:
        print(f"ERROR: {error}")
