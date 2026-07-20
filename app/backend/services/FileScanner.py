
# find files with the information to be added to the database
from pathlib import Path

# Find files with information to be added to the database
class FileScanner:

    def __init__(self, root_folder: str):
        self.root_folder = root_folder

    # finds the excel files
    def find_excel_files(self) -> list:

        # creates the variable files
        files=[]

        # searches recursively for Excel files
        for extension in ("*.xlsx", "*.xls"):
            files.extend(
                Path(self.root_folder).rglob(extension)
            )

        # returns list of file paths
        return files