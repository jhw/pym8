import json
import os
import sys
from pathlib import Path

def compact_json(data):
    """Recursively limit lists to their first three items"""
    if isinstance(data, list):
        # Limit list to first three items
        return [compact_json(item) for item in data[:3]]
    elif isinstance(data, dict):
        # Process each key-value pair in the dictionary
        return {key: compact_json(value) for key, value in data.items()}
    else:
        # Return primitive values unchanged
        return data

def main():
    # Check if a filename was provided
    if len(sys.argv) < 2:
        print("Error: Please provide a path to a JSON file")
        sys.exit(1)
    
    input_path = Path(sys.argv[1])
    
    # Check if the file exists
    if not input_path.exists():
        print(f"Error: File not found: {input_path}")
        sys.exit(1)
    
    # Check if the file is a JSON file
    if input_path.suffix.lower() != '.json':
        print(f"Warning: File does not have .json extension: {input_path}")
    
    # Create tmp directory if it doesn't exist
    tmp_dir = Path('tmp')
    tmp_dir.mkdir(exist_ok=True)
    
    # Output file path (name-minified.json in tmp directory)
    stem = input_path.stem  # Get filename without extension
    output_path = tmp_dir / f"{stem}-minified.json"
    
    try:
        # Load JSON data
        with open(input_path, 'r') as file:
            data = json.load(file)
        
        # Compact data by limiting lists to first three items
        compacted_data = compact_json(data)
        
        # Save compacted data
        with open(output_path, 'w') as file:
            json.dump(compacted_data, file, indent=2)
        
        print(f"Successfully compacted JSON and saved to {output_path}")
    
    except json.JSONDecodeError:
        print(f"Error: {input_path} is not a valid JSON file")
        sys.exit(1)
    except Exception as e:
        print(f"Error processing file: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
