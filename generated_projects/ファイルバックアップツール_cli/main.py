import os
import sys
from pathlib import Path

class BackupTool:
    def __init__(self, src_path):
        self.src_path = Path(src_path)

    def backup(self, dest_path="backup"):
        if not self.src_path.exists():
            print(f"Error: {self.src_path} does not exist.")
            return

        try:
            # Copy file
            copy_file(self.src_path, os.path.join(dest_path, self.src_path.name))
            print(f"{self.src_path} has been backed up to {dest_path}")
        except Exception as e:
            print(f"Error: {e}")

def copy_file(src_path, dest_path):
    if not src_path.exists():
        raise FileNotFoundError(f"The source path '{src_path}' does not exist.")

    try:
        shutil.copy2(src_path, dest_path)
    except OSError as e:
        raise Exception(f"Could not back up the file: {e}")

def help_message():
    print("Usage:")
    print("-h or --help")
    print("Example:")
    print("$ python3 backup_tool.py /path/to/source")
    print("$ python3 backup_tool.py --backup /path/to/destination")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        src_path = sys.argv[1]
        tool = BackupTool(src_path)
        tool.backup()
    else:
        help_message()

# TODO: Implement additional features like deleting old backups or checking the progress of each backup