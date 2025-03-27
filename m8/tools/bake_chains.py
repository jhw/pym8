#!/usr/bin/env python3
import argparse
import os
import sys

from m8.api import M8ValidationResult
from m8.api.project import M8Project
from m8.api.chains import M8Chain, M8ChainStep
from m8.api.song import M8SongRow


class ChainBaker:
    """Tool for baking chains in an M8 project."""
    
    def __init__(self, options=None):
        """Initialize with optional configuration options."""
        self.options = options or {}
        self.project = None
        self.blocks = []
        self.selected_blocks = []
    
    def identify_chain_blocks(self, song):
        """Find square blocks of chain IDs in the song matrix."""
        blocks = []
        current_block = []
        current_block_start_row = 0
        
        for row_idx, row in enumerate(song):
            # If this row is empty and we have a current block, process it
            if row.is_empty():
                if current_block:
                    blocks.append((current_block_start_row, current_block))
                    current_block = []
                continue
                
            # Find chain references in this row
            chain_refs = []
            for col_idx in range(len(row._data)):
                if row[col_idx] != row.EMPTY_CHAIN:
                    chain_refs.append((col_idx, row[col_idx]))
            
            # If we have chain references, add them to the current block
            if chain_refs:
                if not current_block:
                    current_block_start_row = row_idx
                current_block.append(chain_refs)
        
        # Add the last block if there is one
        if current_block:
            blocks.append((current_block_start_row, current_block))
        
        self.blocks = blocks
        return blocks
    
    @staticmethod
    def validate_block_is_square(block):
        """
        Check if a block is a perfect square matrix.
        
        Args:
            block: List of rows where each row is a list of (col_idx, chain_id) tuples
            
        Returns:
            Tuple of (rows, cols) dimensions
            
        Raises:
            ValueError: If block is not square
        """
        # Check if all rows have the same number of elements
        if not block:
            return 0, 0
            
        first_row_len = len(block[0])
        if first_row_len == 0:
            return 0, 0
            
        for row in block:
            if len(row) != first_row_len:
                raise ValueError("Block is not rectangular")
        
        # Check if block is square
        if len(block) != first_row_len:
            raise ValueError("Block is not square")
        
        return len(block), first_row_len
    
    def prompt_for_blocks(self):
        """Ask user to select blocks for processing."""
        selected_blocks = []
        
        print(f"Found {len(self.blocks)} chain blocks:")
        for block_idx, (start_row, block) in enumerate(self.blocks):
            try:
                rows, cols = self.validate_block_is_square(block)
                print(f"Block {block_idx+1}: {rows}x{cols} matrix starting at row {start_row}")
                
                # Show the chains in the block
                for row_idx, row in enumerate(block):
                    chain_ids = [f"{chain_id:02X}" for _, chain_id in row]
                    print(f"  Row {row_idx}: {' '.join(chain_ids)}")
                    
                while True:
                    response = input(f"Include Block {block_idx+1}? (y/n/q to quit): ").lower()
                    if response == 'y':
                        selected_blocks.append((start_row, block))
                        break
                    elif response == 'n':
                        break
                    elif response == 'q':
                        print("Operation cancelled by user.")
                        return []
                    else:
                        print("Please enter 'y', 'n', or 'q'.")
            except ValueError as e:
                print(f"Block {block_idx+1} at row {start_row} is invalid: {e}")
        
        self.selected_blocks = selected_blocks
        return selected_blocks
    
    @staticmethod
    def calculate_new_id(row, col):
        """Calculate chain ID from row/column position."""
        return (col * 10) + row
    
    def bake_chain_block(self, block_data, target_row):
        """Convert a block of chains into consolidated new chains."""
        start_row, block = block_data
        rows, cols = self.validate_block_is_square(block)
        
        # Create new chains for each column
        new_chain_ids = []
        for col_idx in range(cols):
            # Create a new chain
            new_chain = M8Chain()
            new_chain_id = self.calculate_new_id(target_row, col_idx)
            
            # For each row in this column, add the phrase to the chain
            for step_idx, row in enumerate(block):
                # Get the chain ID from this position in the block
                orig_col_idx, orig_chain_id = row[col_idx]
                
                # Get the phrases from this chain
                orig_chain = self.project.chains[orig_chain_id]
                
                # Since we're working with one-to-one chains, we can simply take the
                # phrase referenced by the chain and add it to our new chain
                if not orig_chain.is_empty():
                    # In one-to-one chains, the first step has a reference to the phrase
                    # with the same ID as the chain
                    phrase_id = orig_chain[0].phrase
                    
                    # Add this phrase reference to our new chain
                    if step_idx < len(new_chain):
                        new_chain[step_idx].phrase = phrase_id
                        new_chain[step_idx].transpose = orig_chain[0].transpose
            
            # Add the new chain
            self.project.set_chain(new_chain, new_chain_id)
            new_chain_ids.append(new_chain_id)
            
            # Place the new chain in the song matrix
            self.project.song[target_row][col_idx] = new_chain_id
        
        # Blank out the original chains in the song matrix
        for row_offset, row in enumerate(block):
            for col_idx, chain_id in row:
                self.project.song[start_row + row_offset][col_idx] = M8ChainStep.EMPTY_PHRASE
        
        return new_chain_ids
    
    def bake_chains(self):
        """Process and combine chains in the project."""
        # Identify chain blocks if not already done
        if not self.blocks:
            self.identify_chain_blocks(self.project.song)
        
        # Prompt user to select blocks if not already done
        if not self.selected_blocks and not self.options.get('skip_prompt', False):
            self.selected_blocks = self.prompt_for_blocks()
        
        if not self.selected_blocks:
            return self.project
        
        # Process the selected blocks
        print("\nBaking chains...")
        
        # Current target row for the new chains
        target_row = 0
        
        for block_data in self.selected_blocks:
            # Find the next available row for placing new chains
            while not self.project.song[target_row].is_empty() and target_row < 255:
                target_row += 1
            
            if target_row >= 255:
                print("Warning: Ran out of rows for new chains. Some blocks may not be processed.")
                break
            
            print(f"Processing block at row {block_data[0]}")
            new_chain_ids = self.bake_chain_block(block_data, target_row)
            print(f"Created new chains: {[f'{id:02X}' for id in new_chain_ids]}")
            
            # Move to the next row for the next block
            target_row += 1
        
        return self.project
    
    def load_project(self, file_path):
        """
        Load an M8 project from file.
        
        Args:
            file_path: Path to M8 project file
            
        Returns:
            Loaded M8Project
            
        Raises:
            IOError: If file doesn't exist or is invalid
            ValueError: If project doesn't have one-to-one chains
        """
        # Validate input file exists
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Input file does not exist: {file_path}")
            
        # Validate input file is an M8 project
        if not file_path.endswith('.m8s'):
            raise ValueError(f"Input file is not an M8 project file: {file_path}")
        
        # Load the project
        try:
            self.project = M8Project.read_from_file(file_path)
            
            # Validate project has one-to-one chains
            result = self.project.validate_one_to_one_chains()
            if not result.valid:
                raise ValueError("Project does not have one-to-one chain structure: " + "\n".join(result.errors))
                
            return self.project
            
        except Exception as e:
            raise IOError(f"Error loading project: {e}")
    
    def save_output(self, output_path=None):
        """
        Save the modified project to file.
        
        Args:
            output_path: Path to save the output project
                         If None, uses a default path based on input path
            
        Returns:
            Path to the saved file
            
        Raises:
            ValueError: If no project is loaded
        """
        if self.project is None:
            raise ValueError("No project loaded. Load a project first.")
            
        # Determine output file path if not provided
        if output_path is None:
            input_path = self.options.get('input_file')
            if input_path:
                base_name = os.path.splitext(input_path)[0]
                output_path = f"{base_name}-baked.m8s"
            else:
                raise ValueError("No output path provided and no input file in options")
        
        # Write output file
        self.project.write_to_file(output_path)
        return output_path
    
    @classmethod
    def from_cli_args(cls, args=None):
        """
        Create an instance from command-line arguments.
        
        Args:
            args: Command line arguments (parsed by argparse)
                 If None, will parse from sys.argv
                 
        Returns:
            Configured ChainBaker instance
        """
        parser = argparse.ArgumentParser(description="Bake chains in an M8 project")
        parser.add_argument("input_file", help="Input M8 project file (.m8s)")
        
        if args is None:
            args = parser.parse_args()
        elif isinstance(args, list):
            args = parser.parse_args(args)
            
        options = {
            'input_file': args.input_file
        }
        
        return cls(options)
    
    def run(self):
        """
        Run the complete chain baking process.
        
        Returns:
            0 for success, 1 for failure
        """
        try:
            # Get input path from options
            input_file = self.options.get('input_file')
            
            # Determine output file path
            base_name = os.path.splitext(input_file)[0]
            output_file = f"{base_name}-baked.m8s"
            
            # Load the project
            try:
                self.load_project(input_file)
            except Exception as e:
                print(f"Error: {e}", file=sys.stderr)
                return 1
            
            # Bake the chains
            self.bake_chains()
            
            # Write output file
            self.save_output(output_file)
            print(f"Successfully created baked project: {output_file}")
            return 0
            
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            return 1


def main():
    """CLI entry point."""
    baker = ChainBaker.from_cli_args()
    return baker.run()


if __name__ == "__main__":
    sys.exit(main())