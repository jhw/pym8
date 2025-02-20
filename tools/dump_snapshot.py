import os

def generate_snapshot(file_list = ["m8/core/__init__.py",
                                   "m8/core/array.py",
                                   "m8/core/list.py",
                                   "m8/core/object.py",
                                   "m8/modulators.py",
                                   "m8/instruments.py",
                                   "m8/phrases.py",
                                   "m8/chains.py",
                                   "m8/song.py",
                                   "m8/project.py",
                                   "tests/object.py",
                                   "demo/read.py",
                                   "demo/write.py"],
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
