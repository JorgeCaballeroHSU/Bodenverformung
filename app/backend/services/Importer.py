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

            




        except:

        finally:

            database.closeConnection()




        # TODO:
        # Insert project
        # Insert location
        # Insert sample
        # Insert test
        # Insert measurements