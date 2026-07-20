# imports required modules/classes
from app.backend.services.FileClassifier import FileClassifier
from app.backend.services.ExcelReader import ExcelReader
from app.backend.services.Parsers import *

# coordinates the processing of the files
class Importer:

    def __init__(self, db):

        self.db = db

    def import_file(self, file_path):

        test_type = \
            FileClassifier.classify(file_path)

        workbook = \
            ExcelReader.load(file_path)

        if test_type == "uniaxial":
            parser = EinaxParser()

        elif test_type == "triaxial":
            parser = TriaxParser()

        else:
            raise Exception(
                "Unknown file type"
            )

        data = parser.parse(workbook)

        self.save_to_database(data)