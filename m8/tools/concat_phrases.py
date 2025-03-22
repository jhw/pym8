#!/usr/bin/env python3
import argparse
import os
import re
import sys

from m8.api.project import M8Project
from m8.api.instruments import M8Instrument, M8Instruments
from m8.api.chains import M8Chain, M8Chains
from m8.api.phrases import M8Phrase, M8Phrases
from m8.api.song import M8SongMatrix


def get_m8s_files(directory, pattern=None):
    """
    Get a list of .m8s files in the specified directory, optionally filtering by pattern.
    """
    if not os.path.exists(directory):
        raise FileNotFoundError(f"Input directory does not exist: {directory}")
        
    if not os.path.isdir(directory):
        raise NotADirectoryError(f"Path is not a directory: {directory}")
    
    # Get all .m8s files
    files = [os.path.join(directory, f) for f in os.listdir(directory) 
             if f.endswith('.m8s') and os.path.isfile(os.path.join(directory, f))]
    
    # Apply regex pattern if provided
    if pattern:
        try:
            regex = re.compile(pattern)
            files = [f for f in files if regex.search(os.path.basename(f))]
        except re.error as e:
            raise ValueError(f"Invalid regex pattern: {e}")
    
    # Sort by modification time (newest first)
    files.sort(key=os.path.getmtime, reverse=True)
    return files


def prompt_for_files(files):
    """
    Prompt the user to select files for processing.
    """
    selected_files = []
    
    print(f"Found {len(files)} .m8s files:")
    for i, file_path in enumerate(files):
        filename = os.path.basename(file_path)
        print(f"[{i+1}] {filename}")
        
    for i, file_path in enumerate(files):
        filename = os.path.basename(file_path)
        while True:
            response = input(f"Include '{filename}'? (y/n/q to quit): ").lower()
            if response == 'y':
                selected_files.append(file_path)
                break
            elif response == 'n':
                break
            elif response == 'q':
                print("Operation cancelled by user.")
                return []
            else:
                print("Please enter 'y', 'n', or 'q'.")
    
    return selected_files


def calculate_new_id(base_id, row, col):
    """
    Calculate new ID based on the M8 row/column pattern.
    In M8, tens digit = column, ones digit = row.
    """
    return (col * 10) + row


def concat_projects(projects):
    """
    Concatenate multiple M8 projects with one-to-one chain structure.
    Projects are arranged vertically in the output.
    """
    if not projects:
        raise ValueError("No projects to concatenate")
    
    # Create a new project based on the first project
    output_project = M8Project.initialise()
    
    # Current project position (for ID remapping)
    current_row = 0
    
    # Mapping of original instrument IDs to new instrument IDs
    instrument_id_mapping = {}
    
    # Process each project
    for project_index, project in enumerate(projects):
        # Validate project has one-to-one chains
        if not project.validate_one_to_one_chains():
            raise ValueError(f"Project {project_index} does not have one-to-one chain structure")
        
        # Process instruments
        for orig_inst_idx, instrument in enumerate(project.instruments):
            if not isinstance(instrument, M8Instrument):
                continue  # Skip empty slots
                
            # Add instrument to output project
            new_inst_idx = output_project.add_instrument(instrument)
            instrument_id_mapping[(project_index, orig_inst_idx)] = new_inst_idx
        
        # Process chains and phrases
        non_empty_chains = [(i, chain) for i, chain in enumerate(project.chains) 
                            if not chain.is_empty()]
        
        for orig_chain_idx, chain in non_empty_chains:
            # Get the corresponding phrase (in one-to-one pattern, phrase ID = chain ID)
            orig_phrase_idx = orig_chain_idx
            phrase = project.phrases[orig_phrase_idx]
            
            # Skip empty phrases
            if phrase.is_empty():
                continue
                
            # Calculate new chain/phrase ID based on row/column pattern
            col = project_index  # Each project gets a column
            row = current_row + (orig_chain_idx % 10)  # Keep the original row within limits
            new_id = calculate_new_id(orig_chain_idx, row, col)
            
            # Remap instrument references in the phrase
            for step in phrase:
                if step.instrument != 0xFF:  # 0xFF = empty instrument
                    orig_inst_id = step.instrument
                    step.instrument = instrument_id_mapping.get((project_index, orig_inst_id), 0xFF)
            
            # Add the phrase and chain to the output project
            output_project.set_phrase(phrase, new_id)
            
            # Create a one-to-one chain
            new_chain = M8Chain()
            new_chain[0].phrase = new_id  # Set the first step to reference our phrase
            output_project.set_chain(new_chain, new_id)
            
            # Add the chain to the song matrix
            output_project.song[row][col] = new_id
        
        # Increment row counter for next project
        # Find the highest row used in this project
        if non_empty_chains:
            highest_row = max(chain_idx % 10 for chain_idx, _ in non_empty_chains)
            current_row += highest_row + 1
    
    return output_project


def main():
    parser = argparse.ArgumentParser(description="Concatenate phrases from multiple M8 projects")
    parser.add_argument("input_dir", help="Directory containing M8 project files")
    parser.add_argument("output_file", help="Output file path for the concatenated project")
    parser.add_argument("--pattern", "-p", help="Regex pattern to filter input files")
    
    args = parser.parse_args()
    
    try:
        # Validate input directory exists
        if not os.path.exists(args.input_dir):
            print(f"Error: Input directory does not exist: {args.input_dir}", file=sys.stderr)
            return 1
            
        # Create output directory if it doesn't exist
        output_dir = os.path.dirname(args.output_file)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        # Get M8S files
        files = get_m8s_files(args.input_dir, args.pattern)
        if not files:
            print(f"No .m8s files found in {args.input_dir}" + 
                  (f" matching pattern '{args.pattern}'" if args.pattern else ""), 
                  file=sys.stderr)
            return 1
        
        # Prompt user to select files
        selected_files = prompt_for_files(files)
        if not selected_files:
            return 1
        
        # Load projects
        projects = []
        for file_path in selected_files:
            try:
                project = M8Project.read_from_file(file_path)
                # Validate one-to-one structure
                if not project.validate_one_to_one_chains():
                    print(f"Warning: {os.path.basename(file_path)} does not follow one-to-one chain structure. Skipping.")
                    continue
                projects.append(project)
            except Exception as e:
                print(f"Error loading {file_path}: {e}", file=sys.stderr)
        
        if not projects:
            print("No valid projects to process.", file=sys.stderr)
            return 1
        
        # Concatenate projects
        output_project = concat_projects(projects)
        
        # Write output file
        output_project.write_to_file(args.output_file)
        print(f"Successfully created concatenated project: {args.output_file}")
        return 0
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())