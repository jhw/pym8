import os

def generate_snapshot(file_list = ["core.py",
                                   "core_array.py",
                                   "core_list.py",
                                   "core_object.py",
                                   "modulators.py",
                                   "instruments.py",
                                   "phrases.py",
                                   "chains.py",
                                   "song.py",
                                   "project.py",
                                   "demo_read.py",
                                   "demo_write.py"],
                      output_filename = "tmp/snapshot.md"):
    with open(output_filename, "w", encoding="utf-8") as md_file:
        md_file.write("Here's a snapshot of the current codebase. Please digest and then I will ask questions and for extensions. There is no need for suggestions for improvements at this time.\n\n")
        for filename in file_list:
            md_file.write(f"# {filename}\n\n")
            md_file.write("```python\n")                
            with open(filename, "r", encoding="utf-8") as f:
                md_file.write(f.read())                
            md_file.write("\n```\n\n")

if __name__ == "__main__":
    generate_snapshot()
