# =====================================================
# main.py
#
# Entry point for the Bodenverformung project.
#
# Responsibilities:
#   1. Define the database location
#   2. Create the database file (if it does not exist)
#   3. Create all required tables
# =====================================================

# Imports required libraries
from database.database import *
from services.Importer import Importer

# defines the main function of the application
def main() -> None:
    """
    Main application entry point.
    """

    # creates database according to the defined schema.
    Schema()

    # defines variable with the filepath
    path_file="/mnt/r/institut/Labor/Projekte/BBI/2018-080_BBI-FBQ-Hinterlandanbindung/1_Auftrag_2018_080/GDS-Einax_BBI_Hinterlandbindung_FBQ_TBW_B2_Mg_14m.xlsx"

    # inserts the information in the database
    # creates an instance of importer that is used to add the information to the database
    importer=Importer()

    # inserts data in the database
    importer.import_file(file_path=path_file)






# runs when executed
if __name__ == "__main__":
    main()