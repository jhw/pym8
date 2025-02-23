from m8 import M8Block
from m8.api.project import M8Project

import sys
import os

def print_project_info(project):
    """Print formatted information about an M8 project, skipping empty elements"""
    print(f"--- version ---")
    print(project.version.as_list())
    
    print(f"--- metadata ---")
    print(project.metadata.as_dict())
    
    print(f"--- song ---")
    for i, row in enumerate(project.song):
        if not row.is_empty():
            print(f"({i})\t{row.as_list()}")
            
    print(f"--- chains ---")
    for i, chain in enumerate(project.chains):
        if not chain.is_empty():
            print(f"Chain {i}:")
            for j, step in enumerate(chain):
                if not step.is_empty():
                    print(f"  ({i},{j})\t{step.as_dict()}")
                    
    print(f"--- phrases ---")
    for i, phrase in enumerate(project.phrases):
        if not phrase.is_empty():
            print(f"Phrase {i}:")
            for j, step in enumerate(phrase):
                if not step.is_empty():
                    print(f"  ({i},{j})\t{step.as_dict()}")

    print(f"--- instruments ---")
    for i, instrument in enumerate(project.instruments):
        if not isinstance(instrument, M8Block):  # Only process actual instruments
            print(f"Instrument {i}:", instrument.as_dict())                

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
    
    project = M8Project.read_from_file(file_path)
    print_project_info(project)

if __name__ == "__main__":
    main()
