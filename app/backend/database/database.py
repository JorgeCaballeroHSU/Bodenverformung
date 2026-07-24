# this files contains the classses for the creation, modification and deletion of the database and its tables

# import required libraries
import sqlite3
from sqlite3 import Error


class Database:
    
    # Class' properties
    filePath:str=''
    
    def __init__(self, dbFile: str="/home/Bodenverformung/app/backend/storage/database.db")->None:
        """ create a database connection to the SQLite database specified by db_file
        :param db_file: database file
        :return: Connection object or None
        """
        # stores the path file where the database is located
        self.filePath=dbFile

        # makes conn None
        self.conn = None

        #return nothing
        return None

    # inserts new items in a table
    def insertItemsTable(self, query: str, values: tuple = ()) -> tuple:
        """ Safely insert data into a table using parameterized queries.

        :param query: SQL INSERT statement with placeholders (?)
        :param values: tuple of values to insert """ 

        try:

            cursor=self.conn.cursor()

            # execute parameterized query
            cursor.execute(query, values)

            # commit changes
            self.conn.commit()

            # gets the last rowID and the row count
            return (cursor.lastrowid, cursor.rowcount)


        # catches errors during execution
        except Error as e:

            # prints errors
            print(f"Error inserting data: {e}")

            # rolls back to previous state
            self.conn.rollback()

            # gets the last rowID and the row count
            return (-1,-1)

    
    # module to fetch information from the database
    def fetchInfo(self, statement: str, values: tuple = ()) -> list:
        try:
            cursor = self.conn.cursor()

            cursor.execute(statement, values)

            fetchedElement = cursor.fetchall()

            return [dict(row) for row in fetchedElement]

        except Error as e:
            print(f'Error fetching data: {e}')
            return []

    # module to update an existing element
    def updateItem(self, updateStatement:str, Values:tuple)->tuple:

        # opens try block to catch errors
        try:

            cursor=self.conn.cursor()

            # executes the given statement
            cursor.execute(updateStatement,Values)

            # commits executed statement
            self.conn.commit()

            # gets the last rowID and the row count
            return(-1, cursor.rowcount)

        # catches errors during execution
        except Error as e:

            # prints the error found
            print(f'Error updating data: {e}')

            # rolls back to previous state
            self.conn.rollback()

            # gets the last rowID and the row count
            return (-1,-1)

    # module to open connection to the database
    def openConnection(self)->None:

        # attempt to connect to the database using the provided file name and print a success message if the connection is successful
        try:
            self.conn = sqlite3.connect(self.filePath)
            self.conn.execute("PRAGMA foreign_keys = ON;")
            self.conn.row_factory = sqlite3.Row

        # catches any errors that occur during the connection process and print the error message
        except Error as e:
            print(e)

        # returns none
        return None

    # module to close connections to the database
    def closeConnection(self)->None:
        """ close the database connection
        """
        if self.conn:
            self.conn.close()
            self.conn=None

        # return nothing
        return None
    
    # fetches the last ID of the table
    def fetchLastID(self, tableName: str, idColumn: str):
        try:
            self.openConnection()

            result = self.fetchInfo(
                f"SELECT MAX({idColumn}) as id FROM {tableName}"
            )

            self.closeConnection()

            if result and result[0]["id"] is not None:
                return result[0]["id"]

            return None

        except Exception as e:
            print(f"Error fetching last ID from {tableName}: {e}")
            return None
        
    def executeStatement(self, statement: str, values: tuple = ()) -> tuple:

        try:

            cursor = self.conn.cursor()

            cursor.execute(statement, values)

            self.conn.commit()

            return (-1, cursor.rowcount)

        except Error as e:

            print(f"Error executing statement: {e}")

            self.conn.rollback()

            return (-1, -1)
    
# class to create the tables
class Schema(Database):

    # creates the tables in the database
    # creates all the tables necessary for running this project. The database table relations can be seen in the document
    # Datenbak - Class Diagram.png
     
    def __init__(self, dbFile: str="/home/Bodenverformung/app/backend/storage/database.db")->None:
        super().__init__(dbFile)

        # opens the connection
        self.openConnection()

        # creates the tables in the database
        self.__createTables(self.TableSchema())

        # closes connection
        self.closeConnection()

    # creates the tables in the database
    def __createTables(self, tableStatements:list)->None:
        """ create tables in the database using the provided SQL statements
        :param tableStatements: list of SQL statements for creating tables
        """
        # opens a try block to catch errors
        try:

            # creates a cursor object to execute SQL statements
            cursor=self.conn.cursor()

            # executes each statement in the provided list of table creation statements
            for statement in tableStatements:
                cursor.execute(statement)

            # commits changes to the database
            self.conn.commit()

        # catches any errors that occur during the table creation process and print the error message
        except Error as e:
            print(f"Error creating tables: {e}")

        # returns none
        return None

    @staticmethod
    def TableSchema()->list:
        """ create a table from the create_table_sql statement
        :return: list of SQL statements for creating tables 
        """
        projects="""CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_number TEXT,
            project_title TEXT,
            description TEXT,
            created_at TEXT
        );"""
                
        locations="""CREATE TABLE IF NOT EXISTS locations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER NOT NULL,
            location_name TEXT,
            depth_from_m REAL,
            depth_to_m REAL,
            FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
        );"""
                
        samples="""CREATE TABLE IF NOT EXISTS samples (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            location_id INTEGER NOT NULL,
            material TEXT,
            water_content REAL,
            density_kg_m3 REAL,
            initial_mass_kg REAL,
            FOREIGN KEY (location_id) REFERENCES locations(id) ON DELETE CASCADE
        );"""

        test="""CREATE TABLE IF NOT EXISTS tests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sample_id INTEGER NOT NULL,
            test_type TEXT,
            test_date TEXT,
            initial_height_mm REAL,
            initial_diameter_mm REAL,
            young_modulus_kpa REAL,
            compressive_strength_kpa REAL,
            failure_strain_pct REAL,
            operator_name TEXT,
            FOREIGN KEY (sample_id) REFERENCES samples(id) ON DELETE CASCADE
        );"""
        
        measurements="""CREATE TABLE IF NOT EXISTS measurements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            test_id INTEGER NOT NULL,
            time_s REAL,
            force_kn REAL,
            displacement_mm REAL,
            sample_height_mm REAL,
            strain_ratio REAL,
            strain_pct REAL,
            stress_kpa REAL,
            strain_at_max_stress_pct REAL,
            FOREIGN KEY (test_id) REFERENCES tests(id) ON DELETE CASCADE);"""

        files="""CREATE TABLE IF NOT EXISTS files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            test_id INTEGER NOT NULL,
            filename TEXT,
            filepath TEXT,
            sha256 TEXT UNIQUE,
            file_size INTEGER,
            import_date TEXT,
            FOREIGN KEY (test_id) REFERENCES tests(id) ON DELETE CASCADE
        );"""

        features="""CREATE TABLE IF NOT EXISTS features (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            feature_name TEXT UNIQUE,
            description TEXT,
            unit TEXT
        );"""

        prediction_experiments="""CREATE TABLE IF NOT EXISTS prediction_experiments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            feature_set_id INTEGER,
            experiment_name TEXT,
            model_type TEXT,
            prediction_target TEXT,
            prediction_horizon INTEGER,
            lookback_steps INTEGER,
            training_samples INTEGER,
            validation_samples INTEGER,
            test_samples INTEGER,
            mae REAL,
            rmse REAL,
            r2 REAL,
            benchmark_mae REAL,
            benchmark_rmse REAL,
            benchmark_r2 REAL,
            created_at TEXT,
            experiment_config TEXT,
            FOREIGN KEY (feature_set_id) REFERENCES feature_sets(id)
        );"""

        experiment_features="""CREATE TABLE IF NOT EXISTS experiment_features (
            experiment_id INTEGER,
            feature_id INTEGER,
            PRIMARY KEY (experiment_id, feature_id),
            FOREIGN KEY (experiment_id) REFERENCES prediction_experiments(id) ON DELETE CASCADE,
            FOREIGN KEY (feature_id) REFERENCES features(id) ON DELETE CASCADE
        );"""

        predictions="""CREATE TABLE IF NOT EXISTS predictions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            experiment_id INTEGER NOT NULL,
            measurement_id INTEGER NOT NULL,
            actual_value REAL,
            predicted_value REAL,
            prediction_error REAL,
            FOREIGN KEY (experiment_id) REFERENCES prediction_experiments(id) ON DELETE CASCADE,
            FOREIGN KEY (measurement_id) REFERENCES measurements(id) ON DELETE CASCADE
        );"""

        feature_sets="""CREATE TABLE IF NOT EXISTS feature_sets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            description TEXT
        );"""

        feature_set_features="""CREATE TABLE IF NOT EXISTS feature_set_features (
            feature_set_id INTEGER,
            feature_id INTEGER,
            PRIMARY KEY (feature_set_id, feature_id),
            FOREIGN KEY (feature_set_id) REFERENCES feature_sets(id) ON DELETE CASCADE,
            FOREIGN KEY (feature_id) REFERENCES features(id) ON DELETE CASCADE
        );"""

        # returns the list of tables to be created
        return  [projects, locations, samples, test, measurements, files, features, feature_sets, 
                 prediction_experiments, experiment_features, predictions, feature_set_features]
    
   

