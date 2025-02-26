from m8 import M8Block
from m8.api.project import M8Project
import sys
import os
import json

def main():
    # Check if file path was provided
    if len(sys.argv) < 2:
        print("Error: Please provide the path to an .m8s file")
        sys.exit(1)
    
    file_path = sys.argv[1]
    
    # Check if file exists
    if not os.path.exists(file_path):
        print(f"Error: File not found: {file_path}")
        sys.exit(1)
    
    # Check file extension
    if not file_path.lower().endswith('.m8s'):
        print(f"Warning: File does not have .m8s extension: {file_path}")
    
    # Read the project
    project = M8Project.read_from_file(file_path)
    
    # Create output JSON file path
    output_path = os.path.splitext(file_path)[0] + '.json'
    
    # Write to JSON file with pretty printing
    project.write_to_json_file(output_path)
    
    print(f"Project successfully exported to {output_path}")

if __name__ == "__main__":
    main()
