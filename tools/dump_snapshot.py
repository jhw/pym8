import os

def get_files_in_directory(directory):
    """Get all Python files in directory (non-recursively)"""
    if not os.path.exists(directory):
        return []
    return [os.path.join(directory, f) for f in os.listdir(directory) 
            if f.endswith('.py') and os.path.isfile(os.path.join(directory, f))]

def prompt_for_directory(directory):
    """Ask user if they want to include files from a directory"""
    while True:
        response = input(f"Include files from {directory}? (y/n): ").lower()
        if response in ['y', 'n']:
            return response == 'y'
        print("Please answer 'y' or 'n'")

def collect_files():
    """Collect files based on user input"""
    root_directories = [
        "m8/utils",
        "m8/core",
        "m8",
        "m8/instruments",
        "tests",
        "demo",
        "tools"
    ]
    
    selected_files = []
    
    for directory in root_directories:
        if prompt_for_directory(directory):
            files = get_files_in_directory(directory)
            if files:
                selected_files.extend(files)
            else:
                print(f"No Python files found in {directory}")
    
    return selected_files

def generate_snapshot(output_filename="tmp/snapshot.md"):
    """Generate a markdown snapshot of selected Python files"""
    file_list = collect_files()
    
    if not file_list:
        print("No files were selected. Exiting.")
        return
    
    # Create output directory if it doesn't exist
    os.makedirs(os.path.dirname(output_filename), exist_ok=True)
    
    print(f"\nGenerating snapshot with {len(file_list)} files...")
    
    with open(output_filename, "w", encoding="utf-8") as md_file:
        md_file.write("Here's a snapshot of the current codebase, a Python library to parse Dirtywave M8 files. Please digest and then I will ask questions and for extensions. There is no need for suggestions for improvements at this time.\n\n")
        
        for filename in sorted(file_list):
            print(f"Processing: {filename}")
            md_file.write(f"# {filename}\n\n")
            md_file.write("```python\n")
            try:
                with open(filename, "r", encoding="utf-8") as f:
                    md_file.write(f.read())
            except Exception as e:
                md_file.write(f"Error reading file: {str(e)}\n")
            md_file.write("\n```\n\n")
    
    print(f"\nSnapshot generated successfully: {output_filename}")

if __name__ == "__main__":
    generate_snapshot()
