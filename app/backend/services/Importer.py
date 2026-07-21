# imports required modules/classes
from app.backend.services.FileClassifier import FileClassifier
from app.backend.services.ExcelReader import ExcelReader
from app.backend.services.Parsers import *
from app.backend.database.database import Database

# coordinates the processing of the files
class Importer:

    def __init__(self, db):

        self.db = db

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
            raise Exception(
                "Unknown file type"
            )

        # parses the data
        data = parser.parse()

        # saves the data in the database
        self.save_to_database(data)

    def save_to_database(self, data: dict) -> None:
        """
        Insert parsed information into the database.
        """
        
        # initializes a database object and opens connection to database.
        database=Database()

        # tries to open connection and execute query
        try:

            # defines the variables with the data required to complete the database' tables
            project = data["project"]
            location = data["location"]
            sample = data["sample"]
            test = data["test"]
            file_data=data["file_data"]
            measurements = data["measurements"]


            # opens connection
            database.openConnection()

            ##### PROJECTS TABLE #####
            # defines query
            query=""" INSERT INTO projects (project_number, project_title, description, created_at) VALUES (?, ?, ?, ?)"""
            
            # defines the values for the query
            values = (project["project_number"], project["project_title"], project["description"], project["created_at"])

            # excutes query and gets the last project_id from the insert
            project_id,_=database.insertItemsTable(query=query, values=values)

            ##### LOCATIONS TABLE #####
            # defines query
            query="""INSERT INTO locations (project_id, location_name, x_coordinate, y_coordinate) VALUES (?, ?, ?, ?)"""

            # defines the values for the query
            values= (project_id, location["location_name"], location["x_coordinate"], location["y_coordinate"])

            # executes query and geets the last id of the insertion
            location_id,_=database.insertItemsTable(query=query,values=values)

            ##### SAMPLE TABLE #####
            # defines the query to insert in samples table
            query = """INSERT INTO samples (location_id, material, depth_from_m, depth_to_m, water_content, density_kg_m3) 
            VALUES (?, ?, ?, ?, ?, ?)"""

            # defines the values for the query
            values = (location_id, sample["material"], sample["depth_from_m"], sample["depth_to_m"], sample["water_content"],
                      sample["density_kg_m3"])
            
            # exceutes the query and gets the last id
            sample_id,_=database.insertItemsTable(query=query,values=values)

            ##### TEST TABLE #####
            # defines the query
            query="""INSERT INTO tests (sample_id, test_type, test_date, initial_height_mm, initial_diameter_mm, young_modulus_kpa,
            compressive_strength_kpa, failure_strain_pct, operator_name) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)"""

            # defines the values for the query
            values=(sample_id, test["test_type"], test["test_date"], test["initial_height_mm"], test["initial_diameter_mm"],
                    test["young_modulus_kpa"], test["compressive_strength_kpa"], test["failure_strain_pct"], test["operator_name"])
            
            # executes the query and gets the last id
            test_id,_=database.insertItemsTable(query=query,values=values)

            ##### FILES TABLE #####
            # defines the query
            query= """INSERT INTO files (test_id, filename, filepath, sha256, file_size, import_date) VALUES (?, ?, ?, ?, ?, ?)"""

            # defines the values of the query
            values = (test_id, file_data["filename"], file_data["filepath"], file_data["sha256"], file_data["file_size"],
                      file_data["import_date"])
            
            # executes query and gets the last id
            _,_=database.insertItemsTable(query=query,values=values)

            ##### FILES TABLE #####
            # defines the query
            query="""INSERT INTO measurements (test_id, time_s, force_kn, displacement_mm, strain_pct, stress_kpa,
               deviator_stress_kpa, pore_pressure_kpa, effective_stress_kpa) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)"""
            
            # defines the values of the query and insert them in the database
            for row in measurements:

                values = (test_id, row["time_s"], row["force_kn"], row["displacement_mm"], row["strain_pct"], 
                          row["stress_kpa"], row["deviator_stress_kpa"], row["pore_pressure_kpa"],row["effective_stress_kpa"])

                # inserts values in the database
                self.db.insertItemsTable(query=query, values=values)

        # catches erros
        except Exception as e:

            # informs about the error
            print("An error has occurred: {}".format(e))

        finally:
            
            # closes the database
            database.closeConnection()