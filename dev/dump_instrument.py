#!/usr/bin/env python

import os
import sys
import json
from m8.api.project import M8Project

def main():
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <path_to_m8s_file>")
        sys.exit(1)
    
    m8s_path = sys.argv[1]
    
    if not os.path.exists(m8s_path):
        print(f"Error: File not found: {m8s_path}")
        sys.exit(1)
    
    # Load the M8S file and create a project
    project = M8Project.read_from_file(m8s_path)
    
    # Print the first instrument as dict
    if project.instruments and len(project.instruments) > 0:
        print(json.dumps(project.instruments[0].as_dict(), indent=2))
    else:
        print("No instruments found in the project")

if __name__ == "__main__":
    main()