from m8.api import json_dumps
from m8.api.project import M8Project

import sys
import os

def main():
    # Check if file path was provided
    if len(sys.argv) < 2:
        print("Error: Please provide the path to an .json file")
        sys.exit(1)
    
    file_path = sys.argv[1]
    
    # Check if file exists
    if not os.path.exists(file_path):
        print(f"Error: File not found: {file_path}")
        sys.exit(1)
    
    # Check file extension
    if not file_path.lower().endswith('.json'):
        print(f"Warning: File does not have .m8s extension: {file_path}")
    
    # Read the project
    project = M8Project.read_from_json_file(file_path)
    
    # dump
    print(json_dumps(project.as_dict()))

if __name__ == "__main__":
    main()
