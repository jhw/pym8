import os
import sys
import cmd

from m8.api.project import OFFSETS

# Default state variables
DEFAULT_COLS = 16
DEFAULT_ROWS = 16


def hex_dump(data, width: int = 16):
    """Prints data in a readable hex dump format."""
    for i in range(0, len(data), width):
        chunk = data[i:i+width]
        hex_values = ' '.join(f"{b:02X}" for b in chunk)
        ascii_values = ''.join(chr(b) if 32 <= b < 127 else '.' for b in chunk)
        print(f"{i:08X}  {hex_values:<{width * 3}} |{ascii_values}|")


class M8CLI(cmd.Cmd):
    """Command-line interface for interacting with a raw M8S file."""
    
    intro = "M8S File CLI. Type 'help' or '?' for commands."
    prompt = "M8> "

    def __init__(self, file_name):
        super().__init__()
        self.file_name = file_name
        with open(file_name, "rb") as f:
            self.data = f.read()
        self.cols = DEFAULT_COLS
        self.rows = DEFAULT_ROWS

    def do_dump(self, arg):
        """Dump hex data from an offset. Usage: dump <offset_name> [offset]"""
        args = arg.split()
        if not args:
            print("ERROR: Please provide an offset name.")
            return
        
        offset_name = args[0]
        additional_offset = int(args[1]) if len(args) > 1 else 0  # Default additional offset is 0

        if offset_name not in OFFSETS:
            print(f"ERROR: Offset '{offset_name}' not found.")
            return

        base_offset = OFFSETS[offset_name]
        total_offset = base_offset + additional_offset
        length = self.rows * self.cols

        print(f"Dumping {length} bytes from offset '{offset_name}' (0x{total_offset:08X})\n")
        hex_dump(self.data[total_offset:total_offset + length], width=self.cols)

    def do_set_cols(self, arg):
        """Set the number of columns for hex dump. Usage: set_cols <number>"""
        try:
            cols = int(arg)
            if cols <= 0:
                raise ValueError
            self.cols = cols
            print(f"Columns set to {self.cols}")
        except ValueError:
            print("ERROR: Please enter a valid positive integer.")

    def do_set_rows(self, arg):
        """Set the number of rows for hex dump. Usage: set_rows <number>"""
        try:
            rows = int(arg)
            if rows <= 0:
                raise ValueError
            self.rows = rows
            print(f"Rows set to {self.rows}")
        except ValueError:
            print("ERROR: Please enter a valid positive integer.")

    def do_show_config(self, _):
        """Show the current configuration for rows and cols."""
        print(f"Current Configuration:\n - Rows: {self.rows}\n - Columns: {self.cols}")

    def do_exit(self, _):
        """Exit the CLI."""
        print("Exiting M8 CLI.")
        return True


if __name__ == "__main__":
    try:
        if len(sys.argv) < 2:
            raise RuntimeError("Please enter a file name.")
        
        file_name = sys.argv[1]
        
        if not file_name.endswith(".m8s"):
            raise RuntimeError("File must be a .m8s file.")
        
        if not os.path.exists(file_name):
            raise RuntimeError("File does not exist.")
        
        cli = M8CLI(file_name)
        cli.cmdloop()
    
    except RuntimeError as error:
        print(f"ERROR: {error}")
