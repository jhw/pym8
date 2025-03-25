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


class PhrasesConcatenator:
    """Tool for concatenating phrases from multiple M8 projects."""
    
    def __init__(self, options=None):
        """Initialize with optional configuration options."""
        self.options = options or {}
        self.projects = []
        self.output_project = None
    
    def find_m8s_files(self, directory, pattern=None):
        """
        Get a list of .m8s files in the specified directory, optionally filtering by pattern.
        
        Args:
            directory: Path to search for M8 project files
            pattern: Optional regex pattern to filter filenames
            
        Returns:
            List of absolute paths to M8 project files
            
        Raises:
            FileNotFoundError: If directory doesn't exist
            NotADirectoryError: If path is not a directory
            ValueError: If regex pattern is invalid
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
    
    def prompt_for_files(self, files):
        """
        Prompt the user to select files for processing.
        
        Args:
            files: List of file paths to choose from
            
        Returns:
            List of selected file paths
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
    
    def load_projects(self, file_paths):
        """
        Load M8 projects from given file paths.
        
        Args:
            file_paths: List of paths to M8 project files
            
        Returns:
            List of loaded M8Project objects
            
        Raises:
            ValueError: If a project doesn't have one-to-one chain structure
        """
        self.projects = []
        
        for file_path in file_paths:
            try:
                project = M8Project.read_from_file(file_path)
                # Validate one-to-one structure
                if not project.validate_one_to_one_chains():
                    print(f"Warning: {os.path.basename(file_path)} does not follow one-to-one chain structure. Skipping.")
                    continue
                self.projects.append(project)
            except Exception as e:
                print(f"Error loading {file_path}: {e}", file=sys.stderr)
                
        return self.projects
    
    @staticmethod
    def calculate_new_id(base_id, row, col):
        """
        Calculate new ID based on the M8 row/column pattern.
        In M8, tens digit = column, ones digit = row.
        
        Args:
            base_id: Original ID (optional, not used in default implementation)
            row: Row position (0-9)
            col: Column position (0-25)
            
        Returns:
            New ID value
        """
        return (col * 10) + row
    
    def concatenate(self):
        """
        Concatenate loaded projects with one-to-one chain structure.
        Projects are arranged vertically in the output.
        
        Returns:
            The concatenated M8Project
            
        Raises:
            ValueError: If no projects to concatenate
        """
        if not self.projects:
            raise ValueError("No projects to concatenate")
        
        # Create a new project based on the first project
        self.output_project = M8Project.initialise()
        
        # Current project position (for ID remapping)
        current_row = 0
        
        # Mapping of original instrument IDs to new instrument IDs
        instrument_id_mapping = {}
        
        # Process each project
        for project_index, project in enumerate(self.projects):
            # Validate project has one-to-one chains
            if not project.validate_one_to_one_chains():
                raise ValueError(f"Project {project_index} does not have one-to-one chain structure")
            
            # Process instruments
            for orig_inst_idx, instrument in enumerate(project.instruments):
                if not isinstance(instrument, M8Instrument):
                    continue  # Skip empty slots
                    
                # Add instrument to output project
                new_inst_idx = self.output_project.add_instrument(instrument)
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
                new_id = self.calculate_new_id(orig_chain_idx, row, col)
                
                # Remap instrument references in the phrase
                for step in phrase:
                    if step.instrument != 0xFF:  # 0xFF = empty instrument
                        orig_inst_id = step.instrument
                        step.instrument = instrument_id_mapping.get((project_index, orig_inst_id), 0xFF)
                
                # Add the phrase and chain to the output project
                self.output_project.set_phrase(phrase, new_id)
                
                # Create a one-to-one chain
                new_chain = M8Chain()
                new_chain[0].phrase = new_id  # Set the first step to reference our phrase
                self.output_project.set_chain(new_chain, new_id)
                
                # Add the chain to the song matrix
                self.output_project.song[row][col] = new_id
            
            # Increment row counter for next project
            # Find the highest row used in this project
            if non_empty_chains:
                highest_row = max(chain_idx % 10 for chain_idx, _ in non_empty_chains)
                current_row += highest_row + 1
        
        return self.output_project
    
    def save_output(self, output_path):
        """
        Save the concatenated project to the specified path.
        
        Args:
            output_path: Path to save the output project
            
        Raises:
            ValueError: If no output project has been created
        """
        if self.output_project is None:
            raise ValueError("No output project to save. Run concatenate() first.")
            
        # Create output directory if it doesn't exist
        output_dir = os.path.dirname(output_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
        # Write output file
        self.output_project.write_to_file(output_path)
        return output_path
    
    @classmethod
    def from_cli_args(cls, args=None):
        """
        Create an instance from command-line arguments.
        
        Args:
            args: Command line arguments (parsed by argparse)
                 If None, will parse from sys.argv
                 
        Returns:
            Configured PhrasesConcatenator instance
        """
        parser = argparse.ArgumentParser(description="Concatenate phrases from multiple M8 projects")
        parser.add_argument("input_dir", help="Directory containing M8 project files")
        parser.add_argument("output_file", help="Output file path for the concatenated project")
        parser.add_argument("--pattern", "-p", help="Regex pattern to filter input files")
        
        if args is None:
            args = parser.parse_args()
        elif isinstance(args, list):
            args = parser.parse_args(args)
            
        options = {
            'input_dir': args.input_dir,
            'output_file': args.output_file,
            'pattern': args.pattern
        }
        
        return cls(options)
    
    def run(self):
        """
        Run the complete concatenation process.
        
        Returns:
            0 for success, 1 for failure
        """
        try:
            # Get input and output paths from options
            input_dir = self.options.get('input_dir')
            output_file = self.options.get('output_file')
            pattern = self.options.get('pattern')
            
            # Validate input directory exists
            if not os.path.exists(input_dir):
                print(f"Error: Input directory does not exist: {input_dir}", file=sys.stderr)
                return 1
                
            # Get M8S files
            files = self.find_m8s_files(input_dir, pattern)
            if not files:
                print(f"No .m8s files found in {input_dir}" + 
                      (f" matching pattern '{pattern}'" if pattern else ""), 
                      file=sys.stderr)
                return 1
            
            # Prompt user to select files
            selected_files = self.prompt_for_files(files)
            if not selected_files:
                return 1
            
            # Load projects
            self.load_projects(selected_files)
            
            if not self.projects:
                print("No valid projects to process.", file=sys.stderr)
                return 1
            
            # Concatenate projects
            self.concatenate()
            
            # Write output file
            self.save_output(output_file)
            print(f"Successfully created concatenated project: {output_file}")
            return 0
            
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            return 1


def main():
    """CLI entry point."""
    tool = PhrasesConcatenator.from_cli_args()
    return tool.run()


if __name__ == "__main__":
    sys.exit(main())