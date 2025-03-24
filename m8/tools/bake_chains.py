#!/usr/bin/env python3
import argparse
import os
import sys

from m8.api.project import M8Project
from m8.api.chains import M8Chain, M8ChainStep
from m8.api.song import M8SongRow

def identify_chain_blocks(song):
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
    
    return blocks

def validate_block_is_square(block):
    """Check if a block is a perfect square matrix."""
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

def prompt_for_blocks(blocks, project):
    """Ask user to select blocks for processing."""
    selected_blocks = []
    
    print(f"Found {len(blocks)} chain blocks:")
    for block_idx, (start_row, block) in enumerate(blocks):
        try:
            rows, cols = validate_block_is_square(block)
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
    
    return selected_blocks

def calculate_new_id(row, col):
    """Calculate chain ID from row/column position."""
    return (col * 10) + row

def bake_chain_block(project, block_data, target_row):
    """Convert a block of chains into consolidated new chains."""
    start_row, block = block_data
    rows, cols = validate_block_is_square(block)
    
    # Create new chains for each column
    new_chain_ids = []
    for col_idx in range(cols):
        # Create a new chain
        new_chain = M8Chain()
        new_chain_id = calculate_new_id(target_row, col_idx)
        
        # For each row in this column, add the phrase to the chain
        for step_idx, row in enumerate(block):
            # Get the chain ID from this position in the block
            orig_col_idx, orig_chain_id = row[col_idx]
            
            # Get the phrases from this chain
            orig_chain = project.chains[orig_chain_id]
            
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
        project.set_chain(new_chain, new_chain_id)
        new_chain_ids.append(new_chain_id)
        
        # Place the new chain in the song matrix
        project.song[target_row][col_idx] = new_chain_id
    
    # Blank out the original chains in the song matrix
    for row_offset, row in enumerate(block):
        for col_idx, chain_id in row:
            project.song[start_row + row_offset][col_idx] = M8ChainStep.EMPTY_PHRASE
    
    return new_chain_ids

def bake_chains(project):
    """Process and combine chains in the project."""
    # Identify chain blocks
    blocks = identify_chain_blocks(project.song)
    
    # Prompt user to select blocks
    selected_blocks = prompt_for_blocks(blocks, project)
    if not selected_blocks:
        return project
    
    # Process the selected blocks
    print("\nBaking chains...")
    
    # Current target row for the new chains
    target_row = 0
    
    for block_data in selected_blocks:
        # Find the next available row for placing new chains
        while not project.song[target_row].is_empty() and target_row < 255:
            target_row += 1
        
        if target_row >= 255:
            print("Warning: Ran out of rows for new chains. Some blocks may not be processed.")
            break
        
        print(f"Processing block at row {block_data[0]}")
        new_chain_ids = bake_chain_block(project, block_data, target_row)
        print(f"Created new chains: {[f'{id:02X}' for id in new_chain_ids]}")
        
        # Move to the next row for the next block
        target_row += 1
    
    return project

def main():
    parser = argparse.ArgumentParser(description="Bake chains in an M8 project")
    parser.add_argument("input_file", help="Input M8 project file (.m8s)")
    
    args = parser.parse_args()
    
    try:
        input_file = args.input_file
        
        # Validate input file exists
        if not os.path.exists(input_file):
            print(f"Error: Input file does not exist: {input_file}", file=sys.stderr)
            return 1
            
        # Validate input file is an M8 project
        if not input_file.endswith('.m8s'):
            print(f"Error: Input file is not an M8 project file: {input_file}", file=sys.stderr)
            return 1
            
        # Determine output file path
        base_name = os.path.splitext(input_file)[0]
        output_file = f"{base_name}-baked.m8s"
        
        # Load the project
        try:
            project = M8Project.read_from_file(input_file)
        except Exception as e:
            print(f"Error loading project: {e}", file=sys.stderr)
            return 1
        
        # Validate project has one-to-one chains
        if not project.validate_one_to_one_chains():
            print("Error: Project does not have one-to-one chain structure", file=sys.stderr)
            return 1
            
        # Bake the chains
        output_project = bake_chains(project)
        
        # Write output file
        output_project.write_to_file(output_file)
        print(f"Successfully created baked project: {output_file}")
        return 0
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())