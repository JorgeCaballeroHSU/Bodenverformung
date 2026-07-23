# imports required modules/classes
from services.FileClassifier import FileClassifier
from services.ExcelReader import ExcelReader
from services.Parsers import *
from database.database import Database
from pathlib import Path
from datetime import datetime
import hashlib

def calculate_sha256(filepath: str) -> str:

    sha256 = hashlib.sha256()

    with open(filepath, "rb") as file:

        while chunk := file.read(8192):
            sha256.update(chunk)

    return sha256.hexdigest()

# coordinates the processing of the files
class Importer():
    
    # constructor
    def __init__(self):
        
        self.database = Database()

    def import_file(self, file_path):

        # gets the test type and the workbook type
        test_type = FileClassifier.classify(file_path)
        workbook = ExcelReader.load(file_path)

        # checks the type of test
        if test_type == "uniaxial":
            parser = EinaxParser(workbook=workbook)

        elif test_type == "triaxial":
            parser = TriaxParser(workbook=workbook)

        else:
            
            raise ValueError(
                f"Unknown file type: {file_path}"
            )

        file_data = {
            "filename": Path(file_path).name,
            "filepath": str(file_path),
            "sha256": calculate_sha256(file_path),
            "file_size": Path(file_path).stat().st_size,
            "import_date": datetime.now().isoformat()
        }

        # parses the data
        data = parser.parse()

        # saves the data in the database
        self.save_to_database(data, file_data)

    def save_to_database(self, data: dict, file_data:dict) -> dict:
        """
        Insert parsed information into the database.
        """
    
        # tries to open connection and execute query
        try:

            # defines the variables with the data required to complete the database' tables
            project = data["project"]
            location = data["location"]
            sample = data["sample"]
            test = data["test"]
            measurements = data["measurements"]

            # opens connection
            self.database.openConnection()

            ##### PROJECTS TABLE #####
            # defines query
            query=""" INSERT INTO projects (project_number, project_title, description, created_at) VALUES (?, ?, ?, ?)"""
            
            # defines the values for the query
            values = (project["project_number"], project["project_title"], project["description"], project["created_at"])

            # excutes query and gets the last project_id from the insert
            project_id,_=self.database.insertItemsTable(query=query, values=values)

            ##### LOCATIONS TABLE #####
            # defines query
            query="""INSERT INTO locations (project_id, location_name, depth_from_m, depth_to_m) VALUES (?, ?, ?, ?)"""

            # defines the values for the query
            values= (project_id, location["location_name"], location["depth_from_m"], location["depth_to_m"])

            # executes query and geets the last id of the insertion
            location_id,_=self.database.insertItemsTable(query=query,values=values)

            ##### SAMPLE TABLE #####
            # defines the query to insert in samples table
            query = """INSERT INTO samples (location_id, material, water_content, density_kg_m3, initial_mass_kg)
            VALUES (?, ?, ?, ?, ?)"""

            # defines the values for the query
            values = (location_id, sample["material"], sample["water_content"], sample["density_kg_m3"], sample["initial_mass_kg"])

            # exceutes the query and gets the last id
            sample_id,_=self.database.insertItemsTable(query=query,values=values)

            ##### TEST TABLE #####
            # defines the query
            query="""INSERT INTO tests (sample_id, test_type, test_date, initial_height_mm, initial_diameter_mm, young_modulus_kpa,
            compressive_strength_kpa, failure_strain_pct, operator_name) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)"""

            # defines the values for the query
            values=(sample_id, test["test_type"], test["test_date"], test["initial_height_mm"], test["initial_diameter_mm"],
                    test["young_modulus_kpa"], test["compressive_strength_kpa"], test["failure_strain_pct"], test["operator_name"])
            
            # executes the query and gets the last id
            test_id,_=self.database.insertItemsTable(query=query,values=values)

            ##### FILES TABLE #####
            # defines the query
            query= """INSERT INTO files (test_id, filename, filepath, sha256, file_size, import_date) VALUES (?, ?, ?, ?, ?, ?)"""

            # defines the values of the query
            values = (test_id, file_data["filename"], file_data["filepath"], file_data["sha256"], file_data["file_size"],
                      file_data["import_date"])
            
            # executes query and gets the last id
            _,_=self.database.insertItemsTable(query=query,values=values)

            ##### MEASUREMENTS TABLE #####
            # defines the query
            query="""INSERT INTO measurements (test_id, time_s, force_kn, displacement_mm, sample_height_mm, strain_ratio, 
            strain_pct, stress_kpa, strain_at_max_stress_pct) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)"""
            
            # defines the values of the query and insert them in the database
            for row in measurements:

                values = (test_id, row["time_s"], row["force_kn"], row["displacement_mm"], row["sample_height_mm"], row["strain_ratio"],
                          row["strain_pct"], row["stress_kpa"], row["strain_at_max_stress_pct"])

                # inserts values in the database
                self.database.insertItemsTable(query=query, values=values)

            # returns statistics            
            return {"project_id": project_id, "location_id": location_id, "sample_id": sample_id, 
                    "test_id": test_id, "measurements": len(measurements)}

        # catches erros
        except Exception as e:

            # rolles back db to past state
            self.database.conn.rollback()

            # informs about the error
            print("An error has occurred: {}".format(e))

        finally:
            
            # closes the database
            self.database.closeConnection()