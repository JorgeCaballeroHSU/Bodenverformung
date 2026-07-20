from openpyxl import load_workbook
from pathlib import Path

# class for reading a workbook
class ExcelReader:

    @staticmethod
    def load(file_path: str):
        
        # gets the filepath 
        file_path = Path(file_path)

        # checks if the file path exists
        if not file_path.exists():

            # if this does not exist, it rises an error
            raise FileNotFoundError(f"File not found: {file_path}")

        # if the filepath exists, try to load the workbook
        try:
            return load_workbook(file_path,data_only=True)

        # if there is a problem with it, the raise an error
        except Exception as e:
            raise RuntimeError(f"Error loading workbook {file_path}: {e}")
