import os
from datetime import datetime

def prompt_for_directory(directory):
   """Ask user if they want to include files from a directory"""
   while True:
       response = input(f"Include files from {directory}? (y/n/q): ").lower()
       if response == 'q':
           return None  # Signal to quit
       if response in ['y', 'n']:
           return response == 'y'
       print("Please answer 'y', 'n', or 'q' to quit")

def process_directory(root_dir, selected_files):
   """Recursively process a directory, returning True to continue, False to quit"""
   response = prompt_for_directory(root_dir)
   if response is None:  # User quit
       return False
   if not response:
       return True

   # Add Python files from current directory
   files = [f for f in os.listdir(root_dir) 
           if f.endswith('.py') and os.path.isfile(os.path.join(root_dir, f))]
   if files:
       selected_files.extend(os.path.join(root_dir, f) for f in files)
   else:
       print(f"No Python files found in {root_dir}")

   # Get subdirectories (excluding __pycache__)
   subdirs = [d for d in os.listdir(root_dir) 
             if os.path.isdir(os.path.join(root_dir, d)) and d != '__pycache__']
   
   # Process each subdirectory
   for d in subdirs:
       should_continue = process_directory(os.path.join(root_dir, d), selected_files)
       if not should_continue:
           return False
   
   return True

def collect_files():
   """Collect files based on user input"""
   root_directories = [
       "m8",
       "tests",
       "examples",
       "tools",
      "dev"
   ]
   
   selected_files = []
   
   # Process each root directory completely before moving to next
   for directory in root_directories:
       should_continue = process_directory(directory, selected_files)
       if not should_continue:
           break
   
   return selected_files if selected_files else None

def generate_snapshot():
   """Generate a markdown snapshot of selected Python files"""
   # Generate timestamp filename
   timestamp = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
   output_filename = f"tmp/snapshot-{timestamp}.md"
   
   file_list = collect_files()
   
   if file_list is None:
       print("\nNo files were selected. Process cancelled.")
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
