#!/usr/bin/env python3
import cProfile
import pstats
import io
import sys
import os
from m8.api.project import M8Project

def deserialize_project(file_path):
    """Function to deserialize the project"""
    project = M8Project.read_from_json_file(file_path)
    return project

def main():
    # Check if file path was provided
    if len(sys.argv) < 2:
        print("Error: Please provide the path to a JSON file")
        sys.exit(1)
    
    file_path = sys.argv[1]
    
    # Check if file exists
    if not os.path.exists(file_path):
        print(f"Error: File not found: {file_path}")
        sys.exit(1)
    
    # Create a profile object
    pr = cProfile.Profile()
    
    # Start profiling
    pr.enable()
    
    # Run the deserialization
    try:
        project = deserialize_project(file_path)
        print(f"Successfully deserialized project: {project.metadata.name}")
    except Exception as e:
        print(f"Error during deserialization: {str(e)}")
    
    # Stop profiling
    pr.disable()
    
    # Print sorted stats
    s = io.StringIO()
    ps = pstats.Stats(pr, stream=s).sort_stats('cumulative')
    ps.print_stats(50)  # Print top 50 functions by cumulative time
    print(s.getvalue())
    
    # Also save stats to a file for later analysis
    output_file = "deserialization_profile.txt"
    with open(output_file, "w") as f:
        ps = pstats.Stats(pr, stream=f).sort_stats('cumulative')
        ps.print_stats()
    
    print(f"Detailed profile saved to {output_file}")

if __name__ == "__main__":
    main()
